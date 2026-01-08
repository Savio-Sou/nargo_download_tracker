import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
import os
import re

def parse_semver(version):
    """Parse a semver version string and return a tuple for sorting.
    
    Handles versions like 'v1.0.0-beta.9' and returns a tuple that allows
    proper semver sorting (e.g., beta.2 < beta.10).
    """
    # Remove leading 'v' if present
    version = version.lstrip('v')
    
    # Pattern to match semver: major.minor.patch[-prerelease[.number]]
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9-]+)(?:\.(\d+))?)?$'
    match = re.match(pattern, version)
    
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease_type = match.group(4) or ''
        prerelease_num = int(match.group(5)) if match.group(5) else 0
        
        # Releases without prerelease tags should sort after prereleases
        # e.g., 1.0.0 > 1.0.0-beta.9
        if prerelease_type:
            prerelease_priority = 0  # Prerelease versions
        else:
            prerelease_priority = 1  # Stable releases
        
        return (major, minor, patch, prerelease_priority, prerelease_type, prerelease_num)
    
    # Fallback: unparsable versions sort at the very end
    return (float('inf'), 0, 0, 0, version, 0)

def load_download_history(data_dir="."):
    """Load download history from JSON file"""
    history_file = os.path.join(data_dir, "download_history.json")
    
    if not os.path.exists(history_file):
        print(f"No history file found at {history_file}")
        return {}
    
    with open(history_file, 'r') as f:
        return json.load(f)

def create_time_series_plot(history):
    """Create time series plot of downloads"""
    if not history:
        print("No data available for plotting")
        return
    
    dates = []
    total_downloads = []
    
    for date_str, data in sorted(history.items()):
        dates.append(datetime.strptime(date_str, "%Y-%m-%d"))
        total_downloads.append(data['total_downloads'])
    
    plt.figure(figsize=(12, 6))
    plt.plot(dates, total_downloads, marker='o')
    plt.title('Noir v1.0.0 Total Downloads Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Downloads')
    
    # Format x-axis to show only dates (no times)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.xticks(rotation=45)
    
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('downloads_timeline.png')
    print("Timeline plot saved as downloads_timeline.png")

def create_asset_breakdown(history):
    """Create breakdown by asset type for the 5 most recent releases"""
    if not history:
        print("No data available for asset breakdown")
        return
    
    latest_date = max(history.keys())
    latest_data = history[latest_date]
    
    # Get the 5 most recent releases (sorted by release tag)
    release_tags = sorted(latest_data['releases'].keys(), reverse=True)[:5]
    
    asset_groups = {}
    # Flatten only the 5 most recent releases to get all assets
    for release_tag in release_tags:
        release_data = latest_data['releases'][release_tag]
        for stat in release_data['assets']:
            asset_name = stat['asset_name']
            
            # Determine architecture
            if 'aarch64' in asset_name.lower():
                arch = 'ARM64'
            elif 'x86_64' in asset_name.lower():
                arch = 'x86_64'
            else:
                arch = 'Unknown'
            
            # Determine platform
            if 'linux' in asset_name.lower():
                platform = 'Linux'
            elif 'darwin' in asset_name.lower() or 'macos' in asset_name.lower():
                platform = 'macOS'
            elif 'windows' in asset_name.lower() or '.exe' in asset_name:
                platform = 'Windows'
            else:
                platform = 'Other'
            
            # Combine platform and architecture
            platform_arch = f"{platform} {arch}"
            
            if platform_arch not in asset_groups:
                asset_groups[platform_arch] = 0
            asset_groups[platform_arch] += stat['download_count']
    
    # Create custom autopct function to include download counts
    def make_autopct(values):
        def my_autopct(pct):
            absolute = int(pct/100.*sum(values))
            return f'{pct:.1f}% ({absolute:,})'
        return my_autopct
    
    plt.figure(figsize=(14, 12))
    plt.pie(asset_groups.values(), labels=asset_groups.keys(), 
             autopct=make_autopct(asset_groups.values()), 
             textprops={'fontsize': 9}, startangle=90, radius=0.7,
             pctdistance=0.75, labeldistance=1.2)
    plt.title(f'Download Distribution by Platform & Architecture - 5 Most Recent Releases ({latest_date})', 
              fontsize=12, pad=20)
    plt.tight_layout()
    plt.savefig('downloads_by_platform.png', dpi=150, bbox_inches='tight')
    print("Platform breakdown saved as downloads_by_platform.png")

def create_release_breakdown(history):
    """Create breakdown by release version"""
    if not history:
        print("No data available for release breakdown")
        return
    
    latest_date = max(history.keys())
    latest_data = history[latest_date]
    
    release_groups = {}
    for release_tag, release_data in latest_data['releases'].items():
        release_groups[release_tag] = release_data['total_downloads']
    
    # Sort releases by semver (oldest to newest)
    sorted_releases = sorted(release_groups.items(), key=lambda x: parse_semver(x[0]))
    releases = [item[0] for item in sorted_releases]
    downloads = [item[1] for item in sorted_releases]
    
    plt.figure(figsize=(12, 6))
    
    plt.bar(releases, downloads)
    plt.title(f'Downloads by Release Version ({latest_date})')
    plt.xlabel('Release Version')
    plt.ylabel('Total Downloads')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('downloads_by_release.png')
    print("Release breakdown saved as downloads_by_release.png")

def print_summary(history):
    """Print a text summary of the latest data"""
    if not history:
        print("No data available for summary")
        return
    
    latest_date = max(history.keys())
    latest_data = history[latest_date]
    total_downloads = latest_data['total_downloads']
    
    print(f"\nSummary for {latest_date}:")
    print(f"Total Downloads: {total_downloads:,}")
    
    # Check for daily changes in any asset
    has_daily_changes = False
    daily_total = 0
    for release_tag, release_data in latest_data['releases'].items():
        for stat in release_data['assets']:
            if 'daily_change' in stat:
                has_daily_changes = True
                daily_total += stat.get('daily_change', 0)
    
    if has_daily_changes:
        print(f"Daily Change: {daily_total:+,}")
    
    release_totals = {}
    for release_tag, release_data in latest_data['releases'].items():
        release_totals[release_tag] = release_data['total_downloads']
    
    print("\nTop Releases:")
    for release, downloads in sorted(release_totals.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {release}: {downloads:,} downloads")

if __name__ == "__main__":
    history = load_download_history()
    
    if history:
        print_summary(history)
        create_time_series_plot(history)
        create_asset_breakdown(history)
        create_release_breakdown(history)
    else:
        print("Run noir_download_tracker.py first to collect data")