"""
Main logger orchestration module.
"""
import logging
import signal
import sys
from datetime import datetime, timedelta
import time
from typing import Optional

from src.config import (
    API_URL, API_TIMEOUT, DB_PATH, LOG_FILE, LOG_LEVEL,
    DEFAULT_INTERVAL_MINUTES
)
from src.database import Database
from src.fetcher import StationDataFetcher
from src.analyzer import StationAnalyzer

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class BikeStationLogger:
    """Main orchestrator for bike station data logging."""
    
    def __init__(self):
        self.db = Database(DB_PATH)
        self.fetcher = StationDataFetcher(API_URL, API_TIMEOUT)
        self.analyzer = StationAnalyzer(self.db)
        self._running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False
    
    def run_once(self) -> bool:
        """
        Execute a single data collection cycle.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting single data collection cycle")
        
        # Fetch data from API
        data = self.fetcher.fetch()
        if not data:
            logger.error("Failed to fetch data")
            return False
        
        # Get summary for logging
        summary = self.fetcher.get_station_summary(data)
        logger.info(f"Fetched data: {summary['total_stations']} stations, "
                   f"{summary['total_bikes']} bikes, "
                   f"{summary['stations_empty']} empty stations")
        
        # Process and store active stations
        timestamp = datetime.now()
        active_stations = self.fetcher.get_active_stations(data)
        
        success_count = 0
        for station in active_stations:
            if self.db.insert_snapshot(station, timestamp):
                success_count += 1
                
                # Update zero-bike periods tracking
                self.analyzer.update_zero_bike_periods(
                    station['station_id'],
                    station.get('num_bikes_available', 0),
                    timestamp
                )
        
        logger.info(f"Successfully logged {success_count}/{len(active_stations)} stations")
        return success_count > 0
    
    def run_continuous(self, interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
                      duration_hours: Optional[float] = None):
        """
        Run continuous data collection.
        
        Args:
            interval_minutes: Minutes between collection cycles
            duration_hours: Total hours to run (None for infinite)
        """
        self._running = True
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours) if duration_hours else None
        
        logger.info(f"Starting continuous collection every {interval_minutes} minutes")
        if end_time:
            logger.info(f"Will run until {end_time}")
        
        last_daily_calc = datetime.now().date()
        
        while self._running:
            try:
                # Check if we should stop
                if end_time and datetime.now() >= end_time:
                    logger.info("Reached scheduled end time")
                    break
                
                # Run collection cycle
                cycle_start = time.time()
                success = self.run_once()
                
                if not success:
                    logger.warning("Collection cycle failed, will retry")
                
                # Check if we need to calculate daily stats
                current_date = datetime.now().date()
                if current_date != last_daily_calc:
                    # New day - calculate stats for yesterday
                    logger.info("New day detected, calculating yesterday's stats")
                    self.analyzer.calculate_daily_stats(last_daily_calc)
                    last_daily_calc = current_date
                
                # Wait for next interval
                cycle_duration = time.time() - cycle_start
                wait_time = max(0, interval_minutes * 60 - cycle_duration)
                
                if wait_time > 0 and self._running:
                    logger.debug(f"Waiting {wait_time:.1f} seconds until next cycle")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error in collection cycle: {e}", exc_info=True)
                time.sleep(interval_minutes * 60)  # Wait before retry
        
        self.shutdown()
    
    def calculate_daily_stats(self, date: Optional[datetime] = None):
        """
        Calculate daily statistics.
        
        Args:
            date: Date to calculate stats for (default: yesterday)
        """
        if date is None:
            date = datetime.now() - timedelta(days=1)
        
        target_date = date.date() if isinstance(date, datetime) else date
        logger.info(f"Calculating daily statistics for {target_date}")
        
        result = self.analyzer.calculate_daily_stats(target_date)
        logger.info(f"Calculated stats for {result['stations_processed']}/{result['total_stations']} stations")
        
        return result
    
    def generate_report(self, date: Optional[datetime] = None):
        """
        Generate a daily report.
        
        Args:
            date: Date for report (default: today)
        """
        if date is None:
            date = datetime.now()
        
        target_date = date.date() if isinstance(date, datetime) else date
        logger.info(f"Generating report for {target_date}")
        
        report = self.analyzer.generate_report(target_date)
        
        if 'error' in report:
            logger.error(report['error'])
            return report
        
        # Log summary
        summary = report['summary']
        logger.info(f"Report: {summary['total_stations']} stations, "
                   f"{summary['average_availability_percentage']}% average availability, "
                   f"{summary['total_zero_bike_hours']} total hours with zero bikes")
        
        return report
    
    def shutdown(self):
        """Gracefully shutdown the logger."""
        logger.info("Shutting down bike station logger")
        
        # Close any open zero-bike periods
        self.db.close_all_open_periods(datetime.now())
        
        # Calculate final stats for today
        try:
            self.calculate_daily_stats(datetime.now())
        except Exception as e:
            logger.error(f"Error calculating final stats: {e}")
        
        logger.info("Shutdown complete")