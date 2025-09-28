"""
Database models and operations for bike station data.
"""
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database handler for bike station data."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Station snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS station_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    num_bikes_available INTEGER NOT NULL,
                    num_docks_available INTEGER NOT NULL,
                    is_renting BOOLEAN NOT NULL,
                    is_returning BOOLEAN NOT NULL,
                    last_reported INTEGER,
                    UNIQUE(station_id, timestamp)
                )
            ''')
            
            # Zero bike periods table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS zero_bike_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration_minutes REAL,
                    date DATE NOT NULL
                )
            ''')
            
            # Daily statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    total_bikes_seen INTEGER NOT NULL,
                    max_bikes INTEGER NOT NULL,
                    min_bikes INTEGER NOT NULL,
                    avg_bikes REAL NOT NULL,
                    zero_bike_minutes REAL NOT NULL,
                    num_zero_periods INTEGER NOT NULL,
                    low_bike_minutes REAL DEFAULT 0,
                    availability_percentage REAL DEFAULT 100,
                    UNIQUE(station_id, date)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_snapshots_station_time 
                ON station_snapshots(station_id, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp 
                ON station_snapshots(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_zero_periods_station 
                ON zero_bike_periods(station_id, end_time)
            ''')
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def insert_snapshot(self, station_data: Dict, timestamp: datetime) -> bool:
        """Insert a station snapshot."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO station_snapshots 
                    (station_id, timestamp, num_bikes_available, num_docks_available, 
                     is_renting, is_returning, last_reported)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    station_data['station_id'],
                    timestamp,
                    station_data.get('num_bikes_available', 0),
                    station_data.get('num_docks_available', 0),
                    station_data.get('is_renting', False),
                    station_data.get('is_returning', False),
                    station_data.get('last_reported')
                ))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error inserting snapshot: {e}")
            return False
    
    def get_open_zero_period(self, station_id: str) -> Optional[Tuple[int, datetime]]:
        """Get any open zero-bike period for a station."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, start_time FROM zero_bike_periods 
                WHERE station_id = ? AND end_time IS NULL
                ORDER BY start_time DESC LIMIT 1
            ''', (station_id,))
            
            result = cursor.fetchone()
            if result:
                return result['id'], datetime.fromisoformat(result['start_time'])
            return None
    
    def start_zero_period(self, station_id: str, timestamp: datetime):
        """Start a new zero-bike period."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO zero_bike_periods (station_id, start_time, date)
                VALUES (?, ?, ?)
            ''', (station_id, timestamp, timestamp.date()))
            conn.commit()
            logger.debug(f"Started zero-bike period for station {station_id}")
    
    def end_zero_period(self, period_id: int, timestamp: datetime, duration_minutes: float):
        """End a zero-bike period."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE zero_bike_periods 
                SET end_time = ?, duration_minutes = ?
                WHERE id = ?
            ''', (timestamp, duration_minutes, period_id))
            conn.commit()
            logger.debug(f"Ended zero-bike period {period_id}: {duration_minutes:.2f} minutes")
    
    def get_daily_snapshots(self, station_id: str, target_date: date) -> List[Dict]:
        """Get all snapshots for a station on a specific date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM station_snapshots
                WHERE station_id = ? AND DATE(timestamp) = ?
                ORDER BY timestamp
            ''', (station_id, target_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_zero_periods(self, station_id: str, target_date: date) -> List[Dict]:
        """Get all zero-bike periods for a station on a specific date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM zero_bike_periods
                WHERE station_id = ? AND date = ?
                ORDER BY start_time
            ''', (station_id, target_date))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def upsert_daily_stats(self, stats: Dict):
        """Insert or update daily statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO daily_stats 
                (station_id, date, total_bikes_seen, max_bikes, min_bikes, 
                 avg_bikes, zero_bike_minutes, num_zero_periods, 
                 low_bike_minutes, availability_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stats['station_id'],
                stats['date'],
                stats['total_bikes_seen'],
                stats['max_bikes'],
                stats['min_bikes'],
                stats['avg_bikes'],
                stats['zero_bike_minutes'],
                stats['num_zero_periods'],
                stats.get('low_bike_minutes', 0),
                stats.get('availability_percentage', 100)
            ))
            conn.commit()
    
    def get_daily_stats(self, target_date: date) -> List[Dict]:
        """Get daily statistics for all stations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM daily_stats
                WHERE date = ?
                ORDER BY zero_bike_minutes DESC
            ''', (target_date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_active_stations(self, target_date: date) -> List[str]:
        """Get list of stations that were active on a given date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT station_id 
                FROM station_snapshots 
                WHERE DATE(timestamp) = ? AND is_renting = 1
            ''', (target_date,))
            
            return [row[0] for row in cursor.fetchall()]
    
    def close_all_open_periods(self, timestamp: datetime):
        """Close all open zero-bike periods (for graceful shutdown)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE zero_bike_periods 
                SET end_time = ?, 
                    duration_minutes = (julianday(?) - julianday(start_time)) * 24 * 60
                WHERE end_time IS NULL
            ''', (timestamp, timestamp))
            
            affected = cursor.rowcount
            conn.commit()
            
            if affected > 0:
                logger.info(f"Closed {affected} open zero-bike periods")