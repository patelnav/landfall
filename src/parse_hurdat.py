#!/usr/bin/env python3
"""
HURDAT2 Data Parser

This script parses the HURDAT2 data file and extracts US hurricane landfalls,
filtering for Category 1-5 hurricanes.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import re
from datetime import datetime

def parse_hurdat2(file_path: str) -> pd.DataFrame:
    """
    Parse HURDAT2 data file and return a DataFrame with hurricane landfalls.
    
    Args:
        file_path: Path to the HURDAT2 data file
        
    Returns:
        DataFrame containing filtered hurricane landfall data
    """
    # Initialize lists to store data
    data: List[Dict] = []
    current_storm: Dict = {}
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Check if this is a header line (storm info)
            if line.startswith('AL'):
                # If we have a previous storm, add it to data
                if current_storm and 'entries' in current_storm:
                    data.extend(current_storm['entries'])
                
                # Parse header line
                parts = line.split(',')
                storm_id = parts[0].strip()
                name = parts[1].strip()
                entries = int(parts[2].strip())
                
                current_storm = {
                    'storm_id': storm_id,
                    'name': name if name != 'UNNAMED' else f"{storm_id}",
                    'entries': [],
                    'entries_count': entries
                }
                
            # Data line
            elif current_storm and len(current_storm.get('entries', [])) < current_storm.get('entries_count', 0):
                # Parse data line
                parts = line.split(',')
                date_str = parts[0].strip()
                time_str = parts[1].strip()
                record_id = parts[2].strip()
                status = parts[3].strip()
                lat = parts[4].strip()
                lon = parts[5].strip()
                max_wind = parts[6].strip()
                
                # Convert date and time
                try:
                    dt = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M")
                except ValueError:
                    continue
                
                # Parse latitude/longitude
                try:
                    lat_val = float(lat[:-1]) * (1 if lat[-1] == 'N' else -1)
                    lon_val = float(lon[:-1]) * (1 if lon[-1] == 'E' else -1)
                except (ValueError, IndexError):
                    continue
                
                # Parse max wind
                try:
                    max_wind_val = int(max_wind)
                except ValueError:
                    max_wind_val = 0
                
                # Determine category
                category = 0
                if max_wind_val >= 137:  # Cat 5
                    category = 5
                elif max_wind_val >= 113:  # Cat 4
                    category = 4
                elif max_wind_val >= 96:   # Cat 3
                    category = 3
                elif max_wind_val >= 83:   # Cat 2
                    category = 2
                elif max_wind_val >= 64:   # Cat 1
                    category = 1
                
                # Only include landfall records ('L' in record_id) for hurricanes (category >= 1)
                if 'L' in record_id and category >= 1:
                    current_storm['entries'].append({
                        'datetime': dt,
                        'year': dt.year,
                        'name': current_storm['name'],
                        'latitude': lat_val,
                        'longitude': lon_val,
                        'max_wind_knots': max_wind_val,
                        'category': category
                    })
    
    # Add the last storm's entries
    if current_storm and 'entries' in current_storm:
        data.extend(current_storm['entries'])
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Sort by datetime
    if not df.empty:
        df = df.sort_values('datetime')
    
    return df

def main():
    """Main function to parse HURDAT2 data and save filtered landfalls."""
    # Create data directory if it doesn't exist
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Download HURDAT2 data if not present
    hurdat_path = data_dir / 'hurdat2-1851-2023-051124.txt'
    if not hurdat_path.exists():
        print("Please download the HURDAT2 data file and place it in the data directory.")
        print("Download from: https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-051124.txt")
        return
    
    # Parse the data
    print("Parsing HURDAT2 data...")
    df = parse_hurdat2(str(hurdat_path))
    
    # Save the processed data
    output_path = data_dir / 'us_hurricane_landfalls_cat1_5.csv'
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} landfall records to {output_path}")

if __name__ == '__main__':
    main() 