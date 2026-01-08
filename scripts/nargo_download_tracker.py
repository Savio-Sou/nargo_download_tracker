import requests
import json
import csv
from datetime import datetime
import os
from typing import Dict, List, Optional

class NoirDownloadTracker:
    def __init__(self, github_token: Optional[str] = None):
        self.base_url = "https://api.github.com/repos/noir-lang/noir/releases"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
        
        self.data_dir = "."
    
    def fetch_releases(self) -> List[Dict]:
        """Fetch releases from GitHub API (limited to first 1000 due to API constraints)"""
        releases = []
        page = 1
        # GitHub API only returns first 1000 results (10 pages at 100 per page)
        max_pages = 10
        
        while page <= max_pages:
            response = requests.get(
                f"{self.base_url}?page={page}&per_page=100",
                headers=self.headers
            )
            # Handle 422 error when exceeding 1000 results limit
            if response.status_code == 422:
                print(f"Reached GitHub API limit at page {page}, using {len(releases)} releases fetched so far")
                break
            response.raise_for_status()
            
            page_releases = response.json()
            if not page_releases:
                break
                
            releases.extend(page_releases)
            page += 1
            
        return releases
    
    def filter_v1_releases(self, releases: List[Dict]) -> List[Dict]:
        """Filter only v1.0.0 releases (including betas)"""
        return [
            release for release in releases 
            if release['tag_name'].startswith('v1.0.0')
        ]
    
    def extract_download_stats(self, releases: List[Dict]) -> List[Dict]:
        """Extract download statistics from releases"""
        stats = []
        timestamp = datetime.now().isoformat()
        
        for release in releases:
            release_tag = release['tag_name']
            
            if not release.get('assets'):
                continue
                
            for asset in release['assets']:
                stats.append({
                    'timestamp': timestamp,
                    'release_tag': release_tag,
                    'asset_name': asset['name'],
                    'download_count': asset['download_count'],
                    'asset_size': asset['size'],
                    'asset_url': asset['browser_download_url']
                })
        
        return stats
    
    def save_to_csv(self, stats: List[Dict]):
        """Save asset statistics to CSV file"""
        filename = os.path.join(self.data_dir, "download_history.csv")
        
        file_exists = os.path.exists(filename)
        
        with open(filename, 'a', newline='') as csvfile:
            if stats:
                fieldnames = stats[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header only if file doesn't exist
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(stats)
        
        print(f"Asset data appended to {filename}")
    
    def save_daily_totals_csv(self, stats: List[Dict]):
        """Save daily totals to separate CSV file"""
        filename = os.path.join(self.data_dir, "daily_totals.csv")
        
        file_exists = os.path.exists(filename)
        
        # Calculate total downloads for this day
        total_downloads = sum(stat['download_count'] for stat in stats)
        date_str = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().isoformat()
        
        daily_total_record = {
            'date': date_str,
            'timestamp': timestamp,
            'total_downloads': total_downloads
        }
        
        with open(filename, 'a', newline='') as csvfile:
            fieldnames = ['date', 'timestamp', 'total_downloads']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(daily_total_record)
        
        print(f"Daily total appended to {filename}")
    
    def save_to_json(self, stats: List[Dict]):
        """Save statistics to JSON file with historical data"""
        history_file = os.path.join(self.data_dir, "download_history.json")
        
        history = {}
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate total downloads for this day
        total_downloads = sum(stat['download_count'] for stat in stats)
        
        # Group assets by release tag and calculate release totals
        releases = {}
        for stat in stats:
            release_tag = stat['release_tag']
            if release_tag not in releases:
                releases[release_tag] = {
                    "total_downloads": 0,
                    "assets": []
                }
            releases[release_tag]["assets"].append(stat)
            releases[release_tag]["total_downloads"] += stat['download_count']
        
        # Create day summary with total downloads and grouped releases
        day_data = {
            "total_downloads": total_downloads,
            "releases": releases
        }
        
        history[date_str] = day_data
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"Data appended to {history_file}")
    
    def calculate_daily_changes(self, current_stats: List[Dict]) -> List[Dict]:
        """Calculate daily changes by comparing with previous day's data"""
        history_file = os.path.join(self.data_dir, "download_history.json")
        
        if not os.path.exists(history_file):
            return current_stats
        
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        dates = sorted(history.keys())
        if len(dates) < 1:
            return current_stats
        
        previous_date = dates[-1]
        previous_data = history[previous_date]
        
        # Flatten previous releases data to get all assets
        previous_stats = {}
        for release_tag, release_data in previous_data['releases'].items():
            for stat in release_data['assets']:
                key = f"{stat['release_tag']}_{stat['asset_name']}"
                previous_stats[key] = stat['download_count']
        
        for stat in current_stats:
            key = f"{stat['release_tag']}_{stat['asset_name']}"
            previous_count = previous_stats.get(key, 0)
            stat['daily_change'] = stat['download_count'] - previous_count
        
        return current_stats
    
    def run(self):
        """Main execution method"""
        print("Fetching Noir releases...")
        releases = self.fetch_releases()
        
        print("Filtering v1.0.0 releases...")
        v1_releases = self.filter_v1_releases(releases)
        
        print(f"Found {len(v1_releases)} v1.0.0 releases")
        
        print("Extracting download statistics...")
        stats = self.extract_download_stats(v1_releases)
        
        print("Calculating daily changes...")
        stats_with_changes = self.calculate_daily_changes(stats)
        
        print("Saving data...")
        self.save_to_csv(stats_with_changes)
        self.save_daily_totals_csv(stats_with_changes)
        self.save_to_json(stats_with_changes)
        
        total_downloads = sum(stat['download_count'] for stat in stats)
        print(f"\nSummary:")
        print(f"Total downloads across all v1.0.0 assets: {total_downloads}")
        
        if any('daily_change' in stat for stat in stats_with_changes):
            daily_total = sum(stat.get('daily_change', 0) for stat in stats_with_changes)
            print(f"Downloads in the last 24 hours: {daily_total}")

if __name__ == "__main__":
    github_token = os.environ.get('GITHUB_TOKEN')
    
    tracker = NoirDownloadTracker(github_token)
    tracker.run()