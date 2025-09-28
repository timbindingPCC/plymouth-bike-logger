"""
Configuration settings for the bike station logger.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_URL = os.getenv(
    'GBFS_API_URL',
    'https://gbfs.beryl.cc/v2_2/Plymouth/station_status.json'
)
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))

# Database Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = os.getenv('DB_PATH', str(DATA_DIR / 'bike_station_data.db'))

# Logging Configuration
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = str(LOG_DIR / 'bike_station_logger.log')

# Collection Configuration
DEFAULT_INTERVAL_MINUTES = int(os.getenv('COLLECTION_INTERVAL', '5'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))

# Analysis Configuration
ZERO_BIKE_THRESHOLD = int(os.getenv('ZERO_BIKE_THRESHOLD', '0'))
LOW_BIKE_THRESHOLD = int(os.getenv('LOW_BIKE_THRESHOLD', '2'))