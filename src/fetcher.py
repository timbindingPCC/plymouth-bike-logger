"""
API data fetching module for GBFS bike station data.
"""
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class StationDataFetcher:
    """Fetches bike station data from GBFS API."""
    
    def __init__(self, api_url: str, timeout: int = 10):
        self.api_url = api_url
        self.timeout = timeout
        self._last_fetch_time = None
        self._min_fetch_interval = 1  # Minimum seconds between fetches
    
    def fetch(self) -> Optional[Dict]:
        """
        Fetch current station status from API.
        
        Returns:
            Dictionary containing station data or None if fetch fails
        """
        # Rate limiting
        if self._last_fetch_time:
            elapsed = time.time() - self._last_fetch_time
            if elapsed < self._min_fetch_interval:
                time.sleep(self._min_fetch_interval - elapsed)
        
        try:
            response = requests.get(self.api_url, timeout=self.timeout)
            response.raise_for_status()
            
            self._last_fetch_time = time.time()
            data = response.json()
            
            # Validate response structure
            if not self._validate_response(data):
                logger.error("Invalid response structure")
                return None
            
            logger.info(f"Successfully fetched data for {len(data['data']['stations'])} stations")
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching data from {self.api_url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing response: {e}")
        
        return None
    
    def _validate_response(self, data: Dict) -> bool:
        """Validate GBFS response structure."""
        try:
            # Check required GBFS fields
            if 'data' not in data or 'stations' not in data['data']:
                return False
            
            # Check if we have at least one station
            if not data['data']['stations']:
                logger.warning("No stations in response")
                return False
            
            # Validate first station has required fields
            station = data['data']['stations'][0]
            required_fields = ['station_id', 'num_bikes_available', 'is_renting']
            
            for field in required_fields:
                if field not in station:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            return True
            
        except (KeyError, IndexError, TypeError):
            return False
    
    def get_active_stations(self, data: Dict) -> List[Dict]:
        """
        Filter and return only active (is_renting=true) stations.
        
        Args:
            data: Raw GBFS response data
            
        Returns:
            List of active station dictionaries
        """
        if not data or 'data' not in data:
            return []
        
        stations = data.get('data', {}).get('stations', [])
        active_stations = [
            station for station in stations 
            if station.get('is_renting', False)
        ]
        
        logger.debug(f"Filtered {len(active_stations)} active stations from {len(stations)} total")
        return active_stations
    
    def get_station_summary(self, data: Dict) -> Dict:
        """
        Get summary statistics of current station status.
        
        Args:
            data: Raw GBFS response data
            
        Returns:
            Dictionary with summary statistics
        """
        if not data:
            return {}
        
        stations = self.get_active_stations(data)
        
        if not stations:
            return {
                'total_stations': 0,
                'total_bikes': 0,
                'total_docks': 0,
                'stations_with_bikes': 0,
                'stations_empty': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        total_bikes = sum(s.get('num_bikes_available', 0) for s in stations)
        total_docks = sum(s.get('num_docks_available', 0) for s in stations)
        stations_with_bikes = sum(1 for s in stations if s.get('num_bikes_available', 0) > 0)
        stations_empty = len(stations) - stations_with_bikes
        
        return {
            'total_stations': len(stations),
            'total_bikes': total_bikes,
            'total_docks': total_docks,
            'stations_with_bikes': stations_with_bikes,
            'stations_empty': stations_empty,
            'average_bikes_per_station': total_bikes / len(stations) if stations else 0,
            'timestamp': datetime.now().isoformat()
        }