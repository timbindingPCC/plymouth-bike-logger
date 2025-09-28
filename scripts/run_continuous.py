#!/usr/bin/env python3
"""
Continuous monitoring script for bike station data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import BikeStationLogger
from src.config import DEFAULT_INTERVAL_MINUTES
import argparse


def main():
    parser = argparse.ArgumentParser(description='Run continuous bike station data collection')
    parser.add_argument('--interval', type=int, default=DEFAULT_INTERVAL_MINUTES,
                       help=f'Collection interval in minutes (default: {DEFAULT_INTERVAL_MINUTES})')
    parser.add_argument('--duration', type=float, default=None,
                       help='Total duration in hours (omit for continuous)')
    
    args = parser.parse_args()
    
    print(f"Starting continuous collection every {args.interval} minutes")
    if args.duration:
        print(f"Will run for {args.duration} hours")
    else:
        print("Running continuously (press Ctrl+C to stop)")
    
    # Initialize and run logger
    logger = BikeStationLogger()
    
    try:
        logger.run_continuous(
            interval_minutes=args.interval,
            duration_hours=args.duration
        )
    except KeyboardInterrupt:
        print("\nStopping collection...")
        logger.shutdown()
    
    print("Collection stopped")


if __name__ == "__main__":
    main()