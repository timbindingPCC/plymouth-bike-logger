# Plymouth Bike Station Logger

A Python application that tracks bike availability at Plymouth bike stations using the GBFS (General Bikeshare Feed Specification) API.

## Features

- 📊 Real-time tracking of bike availability at all stations
- ⏱️ Monitors zero-bike availability periods
- 📈 Daily statistics and analytics
- 🗄️ SQLite database for historical data
- 📝 Comprehensive logging
- 🔄 Automated data collection via GitHub Actions

## Project Structure

```
plymouth-bike-logger/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration settings
│   ├── database.py          # Database models and operations
│   ├── fetcher.py          # API data fetching
│   ├── analyzer.py         # Data analysis and statistics
│   └── logger.py           # Main logger orchestration
├── scripts/
│   ├── run_once.py         # Single execution script
│   ├── run_continuous.py   # Continuous monitoring script
│   └── generate_report.py  # Report generation script
├── .github/
│   └── workflows/
│       └── data_collection.yml  # GitHub Actions workflow
├── data/
│   ├── database.db         # database 
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── setup.py
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/plymouth-bike-logger.git
cd plymouth-bike-logger
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Usage

### Single Run
```bash
python scripts/run_once.py
```

### Continuous Monitoring
```bash
python scripts/run_continuous.py --interval 5
```

### Generate Report
```bash
python scripts/generate_report.py --date 2024-01-15
```

## Database Schema

The application uses SQLite with three main tables:

- `station_snapshots`: Time-series data of bike availability
- `zero_bike_periods`: Tracks periods when stations have no bikes
- `daily_stats`: Aggregated daily statistics per station

## Automated Collection

The repository includes GitHub Actions workflow that runs every 5 minutes to collect data automatically. The database is committed back to the repository for persistence.

## Analytics

Query the SQLite database directly for custom analytics:

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/bike_station_data.db')
df = pd.read_sql_query("SELECT * FROM daily_stats", conn)
```

## License

MIT
