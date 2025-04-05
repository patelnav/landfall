#!/usr/bin/env python3
"""
Extract Test Cluster for Phase 2

This script extracts a small cluster of overlapping labels from the South Florida map
for use in Phase 2 of the project.
"""

import pandas as pd
from pathlib import Path

# Constants
PHASE2_OUTPUT_DIR = Path('output') / 'phase2'

def extract_miami_cluster(data_path: str, output_path: str) -> None:
    """
    Extract the Miami area cluster of overlapping labels.
    
    Args:
        data_path: Path to the CSV file containing landfall data
        output_path: Path where to save the extracted cluster data
    """
    # Read the data
    df = pd.read_csv(data_path)
    
    # Define Miami area region for data filtering
    # These coordinates are based on the overlap analysis
    filter_min_lon, filter_max_lon = -80.5, -79.5
    filter_min_lat, filter_max_lat = 25.5, 26.5
    
    # Filter data for Miami area
    miami_df = df[
        (df['longitude'] >= filter_min_lon) & 
        (df['longitude'] <= filter_max_lon) & 
        (df['latitude'] >= filter_min_lat) & 
        (df['latitude'] <= filter_max_lat)
    ]
    
    # Add a small buffer to include nearby points that might overlap
    buffer_lon = 0.2
    buffer_lat = 0.2
    
    # Get the min/max coordinates of the Miami cluster
    min_lon = miami_df['longitude'].min() - buffer_lon
    max_lon = miami_df['longitude'].max() + buffer_lon
    min_lat = miami_df['latitude'].min() - buffer_lat
    max_lat = miami_df['latitude'].max() + buffer_lat
    
    # Extract the cluster with buffer
    cluster_df = df[
        (df['longitude'] >= min_lon) & 
        (df['longitude'] <= max_lon) & 
        (df['latitude'] >= min_lat) & 
        (df['latitude'] <= max_lat)
    ]
    
    print(f"Extracted {len(cluster_df)} points for the Miami cluster")
    
    # Save the cluster data
    cluster_df.to_csv(output_path, index=False)
    print(f"Saved cluster data to {output_path}")

def main():
    """Main function to extract the test cluster."""
    # Create Phase 2 output directory if it doesn't exist
    PHASE2_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    # Define paths
    data_path = Path('data') / 'us_hurricane_landfalls_cat1_5.csv'
    output_path = Path('data') / 'test_cluster_data.csv'
    
    # Check if data exists
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return
    
    # Extract the Miami cluster
    print("Extracting Miami cluster...")
    extract_miami_cluster(str(data_path), str(output_path))

if __name__ == '__main__':
    main() 