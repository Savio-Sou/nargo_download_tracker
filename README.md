# Nargo Download Tracker

Automated tracking of download statistics for Noir's Nargo v1.0.0 releases from the official GitHub repository.

## Features

- **Automated Tracking**: Daily collection via GitHub Actions
- **Data Visualization**: Automated chart generation (timeline, platform distribution, release comparison)
- **Historical Trends**: Tracks download changes over time
- **Multiple Formats**: Data stored in CSV and JSON formats
- **Stable Release Focus**: Specifically tracks all v1.0.0 releases (including betas)
- **Platform Breakdown**: Analyzes downloads by OS and architecture


## Project Structure

```
nargo_download_tracker/
├── scripts/                      # Python scripts
│   ├── nargo_download_tracker.py # Main tracking script
│   └── visualize_downloads.py   # Chart generation
├── requirements.txt              # Python dependencies
├── download_history.csv          # Individual asset data
├── daily_totals.csv              # Daily summaries
├── download_history.json         # Structured data
├── *.png                         # Generated visualization charts
└── .github/workflows/
    └── track-downloads.yml       # Automation workflow
```

## Visualizations

The tracker automatically generates three types of charts:

1. **Timeline Chart** (`downloads_timeline.png`) - Total downloads over time
2. **Platform Distribution** (`downloads_by_platform.png`) - Downloads by platform & architecture for 5 most recent releases
3. **Release Comparison** (`downloads_by_release.png`) - Downloads by release version (chronological order)

## Data Structure

### Files Generated

- `download_history.csv` - Individual asset download data
- `daily_totals.csv` - Daily summary totals only
- `download_history.json` - Structured data grouped by release

### CSV Format (download_history.csv)
```csv
timestamp,release_tag,asset_name,download_count,asset_size,asset_url,daily_change
2025-07-25T12:00:00,v1.0.0-beta.9,nargo-x86_64-unknown-linux-gnu.tar.gz,1234,16690769,https://github.com/.../nargo-x86_64-unknown-linux-gnu.tar.gz,45
```

### JSON Format (download_history.json)
```json
{
  "2025-07-25": {
    "total_downloads": 19701,
    "releases": {
      "v1.0.0-beta.9": {
        "total_downloads": 8,
        "assets": [
          {
            "timestamp": "2025-07-25T12:00:00",
            "release_tag": "v1.0.0-beta.9",
            "asset_name": "nargo-x86_64-unknown-linux-gnu.tar.gz",
            "download_count": 5,
            "asset_size": 16690769,
            "asset_url": "https://github.com/noir-lang/noir/releases/download/v1.0.0-beta.9/nargo-x86_64-unknown-linux-gnu.tar.gz",
            "daily_change": 1
          }
        ]
      }
    }
  }
}
```

## Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nargo_download_tracker
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run manually**
   ```bash
   python scripts/nargo_download_tracker.py
   python scripts/visualize_downloads.py
   ```

## GitHub Action

### Purpose

The workflow automatically:
1. Fetches latest download statistics
2. Calculates daily changes
3. Generates updated visualizations
4. Commits all changes back to repository
5. Runs daily at midnight UTC (customizable)

Perfect for hands-off monitoring of Noir adoption trends!

### Setup

1. **Create a GitHub repository** and push code

2. **Set up a GitHub token**:
   - Create a fine-grained personal access token
   - Repository permissions needed: Contents (Read/Write), Metadata (Read)
   - Add as repository secret named `ACTION_TOKEN`

3. **Automated execution**: The workflow will run daily at midnight UTC once set up, and can also be triggered manually
