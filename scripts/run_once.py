#!/usr/bin/env python3
"""
Single execution script for bike station data collection.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import BikeStationLogger
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Run a single bike station data collection cycle')
    parser.add_argument('--calculate-stats', action='store_true',
                       help='Calculate daily statistics after collection')
    parser.add_argument('--stats-date', type=str,
                       help='Date for statistics calculation (YYYY-MM-DD), default is today')
    
    args = parser.parse_args()
    
    # Initialize and run logger
    logger = BikeStationLogger()
    
    # Run single collection
    success = logger.run_once()
    
    if not success:
        print("Data collection failed")
        sys.exit(1)
    
    # Calculate stats if requested
    if args.calculate_stats:
        stats_date = None
        if args.stats_date:
            stats_date = datetime.strptime(args.stats_date, '%Y-%m-%d')
        
        result = logger.calculate_daily_stats(stats_date)
        print(f"Statistics calculated for {result['stations_processed']} stations")
    
    print("Data collection completed successfully")


if __name__ == "__main__":
    main()