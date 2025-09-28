"""
Data analysis module for bike station statistics.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from src.database import Database
from src.config import ZERO_BIKE_THRESHOLD, LOW_BIKE_THRESHOLD

logger = logging.getLogger(__name__)


class StationAnalyzer:
    """Analyzes bike station data and generates statistics."""
    
    def __init__(self, database: Database):
        self.db = database
    
    def update_zero_bike_periods(self, station_id: str, bikes_available: int, 
                                timestamp: datetime):
        """
        Track and update zero-bike periods for a station.
        
        Args:
            station_id: Station identifier
            bikes_available: Current number of bikes
            timestamp: Current timestamp
        """
        open_period = self.db.get_open_zero_period(station_id)
        
        if bikes_available <= ZERO_BIKE_THRESHOLD:
            # Station has zero (or below threshold) bikes
            if not open_period:
                # Start a new zero-bike period
                self.db.start_zero_period(station_id, timestamp)
        else:
            # Station has bikes available
            if open_period:
                # End the zero-bike period
                period_id, start_time = open_period
                duration_minutes = (timestamp - start_time).total_seconds() / 60
                self.db.end_zero_period(period_id, timestamp, duration_minutes)
    
    def calculate_daily_stats(self, target_date: Optional[date] = None) -> Dict:
        """
        Calculate comprehensive daily statistics for all stations.
        
        Args:
            target_date: Date to calculate stats for (default: today)
            
        Returns:
            Dictionary with summary of calculations
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        stations = self.db.get_active_stations(target_date)
        stats_calculated = 0
        
        for station_id in stations:
            try:
                stats = self._calculate_station_daily_stats(station_id, target_date)
                if stats:
                    self.db.upsert_daily_stats(stats)
                    stats_calculated += 1
            except Exception as e:
                logger.error(f"Error calculating stats for station {station_id}: {e}")
        
        logger.info(f"Calculated daily stats for {stats_calculated} stations on {target_date}")
        
        return {
            'date': target_date,
            'stations_processed': stats_calculated,
            'total_stations': len(stations)
        }
    
    def _calculate_station_daily_stats(self, station_id: str, target_date: date) -> Optional[Dict]:
        """
        Calculate daily statistics for a single station.
        
        Args:
            station_id: Station identifier
            target_date: Date to calculate stats for
            
        Returns:
            Dictionary with station statistics
        """
        snapshots = self.db.get_daily_snapshots(station_id, target_date)
        
        if not snapshots:
            return None
        
        # Basic statistics
        bikes_values = [s['num_bikes_available'] for s in snapshots]
        total_bikes = sum(bikes_values)
        max_bikes = max(bikes_values)
        min_bikes = min(bikes_values)
        avg_bikes = total_bikes / len(bikes_values)
        
        # Zero and low bike period calculations
        zero_periods = self.db.get_daily_zero_periods(station_id, target_date)
        zero_bike_minutes = sum(p['duration_minutes'] or 0 for p in zero_periods)
        num_zero_periods = len(zero_periods)
        
        # Calculate low bike minutes (bikes <= threshold but > 0)
        low_bike_minutes = self._calculate_low_bike_minutes(snapshots)
        
        # Calculate availability percentage (time with bikes > 0)
        total_minutes = 24 * 60  # Minutes in a day
        availability_percentage = ((total_minutes - zero_bike_minutes) / total_minutes * 100 
                                 if total_minutes > 0 else 100)
        
        return {
            'station_id': station_id,
            'date': target_date,
            'total_bikes_seen': total_bikes,
            'max_bikes': max_bikes,
            'min_bikes': min_bikes,
            'avg_bikes': round(avg_bikes, 2),
            'zero_bike_minutes': round(zero_bike_minutes, 2),
            'num_zero_periods': num_zero_periods,
            'low_bike_minutes': round(low_bike_minutes, 2),
            'availability_percentage': round(availability_percentage, 2)
        }
    
    def _calculate_low_bike_minutes(self, snapshots: List[Dict]) -> float:
        """
        Calculate minutes when station had low bikes (but not zero).
        
        Args:
            snapshots: List of station snapshots
            
        Returns:
            Total minutes with low bike availability
        """
        if len(snapshots) < 2:
            return 0
        
        low_minutes = 0
        
        for i in range(1, len(snapshots)):
            prev_snap = snapshots[i-1]
            curr_snap = snapshots[i]
            
            bikes = prev_snap['num_bikes_available']
            
            if 0 < bikes <= LOW_BIKE_THRESHOLD:
                # Calculate time difference
                prev_time = datetime.fromisoformat(prev_snap['timestamp'])
                curr_time = datetime.fromisoformat(curr_snap['timestamp'])
                minutes = (curr_time - prev_time).total_seconds() / 60
                low_minutes += minutes
        
        return low_minutes
    
    def generate_report(self, target_date: Optional[date] = None, 
                       top_n: int = 10) -> Dict:
        """
        Generate a comprehensive daily report.
        
        Args:
            target_date: Date for report (default: today)
            top_n: Number of top/bottom stations to include
            
        Returns:
            Dictionary with report data
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        stats = self.db.get_daily_stats(target_date)
        
        if not stats:
            return {
                'date': target_date,
                'error': 'No data available for this date'
            }
        
        # Overall summary
        total_stations = len(stats)
        total_zero_minutes = sum(s['zero_bike_minutes'] for s in stats)
        avg_availability = sum(s['availability_percentage'] for s in stats) / total_stations
        
        # Identify problematic stations
        worst_availability = sorted(stats, key=lambda x: x['availability_percentage'])[:top_n]
        most_zero_periods = sorted(stats, key=lambda x: x['num_zero_periods'], reverse=True)[:top_n]
        
        # Best performing stations
        best_availability = sorted(stats, key=lambda x: x['availability_percentage'], reverse=True)[:top_n]
        
        return {
            'date': target_date,
            'summary': {
                'total_stations': total_stations,
                'average_availability_percentage': round(avg_availability, 2),
                'total_zero_bike_hours': round(total_zero_minutes / 60, 2),
                'stations_with_zero_periods': sum(1 for s in stats if s['num_zero_periods'] > 0)
            },
            'worst_availability': worst_availability,
            'most_zero_periods': most_zero_periods,
            'best_availability': best_availability,
            'full_stats': stats
        }
    
    def get_station_history(self, station_id: str, days: int = 7) -> List[Dict]:
        """
        Get historical statistics for a specific station.
        
        Args:
            station_id: Station identifier
            days: Number of days of history to retrieve
            
        Returns:
            List of daily statistics
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        history = []
        current_date = start_date
        
        while current_date <= end_date:
            stats = self._calculate_station_daily_stats(station_id, current_date)
            if stats:
                history.append(stats)
            current_date += timedelta(days=1)
        
        return history