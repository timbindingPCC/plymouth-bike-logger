#!/usr/bin/env python3
"""
Report generation script for bike station data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import BikeStationLogger
from datetime import datetime, timedelta
import argparse
import json


def print_report(report):
    """Pretty print a report to console."""
    if 'error' in report:
        print(f"Error: {report['error']}")
        return
    
    print(f"\n{'='*60}")
    print(f"BIKE STATION REPORT - {report['date']}")
    print(f"{'='*60}\n")
    
    # Summary section
    summary = report['summary']
    print("SUMMARY")
    print("-" * 30)
    print(f"Total Stations: {summary['total_stations']}")
    print(f"Average Availability: {summary['average_availability_percentage']}%")
    print(f"Total Zero-Bike Hours: {summary['total_zero_bike_hours']}")
    print(f"Stations with Outages: {summary['stations_with_zero_periods']}")
    
    # Worst performing stations
    print(f"\n\nWORST AVAILABILITY (Bottom 5)")
    print("-" * 30)
    print(f"{'Station ID':<15} {'Availability %':<15} {'Zero Minutes':<15}")
    
    for station in report['worst_availability'][:5]:
        print(f"{station['station_id']:<15} "
              f"{station['availability_percentage']:<15.1f} "
              f"{station['zero_bike_minutes']:<15.1f}")
    
    # Best performing stations
    print(f"\n\nBEST AVAILABILITY (Top 5)")
    print("-" * 30)
    print(f"{'Station ID':<15} {'Availability %':<15} {'Avg Bikes':<15}")
    
    for station in report['best_availability'][:5]:
        print(f"{station['station_id']:<15} "
              f"{station['availability_percentage']:<15.1f} "
              f"{station['avg_bikes']:<15.1f}")
    
    # Most frequent outages
    print(f"\n\nMOST FREQUENT OUTAGES")
    print("-" * 30)
    print(f"{'Station ID':<15} {'# Outages':<15} {'Total Minutes':<15}")
    
    for station in report['most_zero_periods'][:5]:
        print(f"{station['station_id']:<15} "
              f"{station['num_zero_periods']:<15} "
              f"{station['zero_bike_minutes']:<15.1f}")
    
    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Generate report from bike station data')
    parser.add_argument('--date', type=str,
                       help='Report date (YYYY-MM-DD), default is today')
    parser.add_argument('--output', type=str, choices=['console', 'json', 'both'],
                       default='console',
                       help='Output format (default: console)')
    parser.add_argument('--output-file', type=str,
                       help='Output file for JSON format')
    parser.add_argument('--calculate-stats', action='store_true',
                       help='Calculate statistics before generating report')
    
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        report_date = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        report_date = datetime.now()
    
    # Initialize logger
    logger = BikeStationLogger()
    
    # Calculate stats if requested
    if args.calculate_stats:
        print(f"Calculating statistics for {report_date.date()}...")
        result = logger.calculate_daily_stats(report_date)
        print(f"Calculated stats for {result['stations_processed']} stations")
    
    # Generate report
    print(f"Generating report for {report_date.date()}...")
    report = logger.generate_report(report_date)
    
    # Output report
    if args.output in ['console', 'both']:
        print_report(report)
    
    if args.output in ['json', 'both']:
        output_file = args.output_file or f"report_{report_date.date()}.json"
        
        # Convert date objects to strings for JSON serialization
        report_json = json.loads(json.dumps(report, default=str))
        
        with open(output_file, 'w') as f:
            json.dump(report_json, f, indent=2)
        print(f"Report saved to {output_file}")


if __name__ == "__main__":
    main()