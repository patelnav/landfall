#!/usr/bin/env python3
"""
South Florida Hurricane Landfall Map Generator

This script creates a focused map of South Florida hurricane landfalls
with raw text labels placed directly at the landfall points.
"""

import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from typing import Tuple

def create_south_florida_map(data_path: str, output_path: str) -> None:
    """
    Create a focused map of South Florida hurricane landfalls with raw labels.
    
    Args:
        data_path: Path to the CSV file containing landfall data
        output_path: Path where to save the output PNG file
    """
    # Read the data
    df = pd.read_csv(data_path)
    
    # Define Florida region for data filtering
    # Keep the same filter bounds to maintain our 116 landfalls
    filter_min_lon, filter_max_lon = -83.0, -75.0
    filter_min_lat, filter_max_lat = 24.0, 31.0
    
    # Filter data for Florida
    florida_df = df[
        (df['longitude'] >= filter_min_lon) & 
        (df['longitude'] <= filter_max_lon) & 
        (df['latitude'] >= filter_min_lat) & 
        (df['latitude'] <= filter_max_lat)
    ]
    
    print(f"Found {len(florida_df)} landfalls in Florida region")
    
    # Create figure and axes
    plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent to match baseline (showing full East Coast context)
    ax.set_extent([-100, -60, 20, 50], crs=ccrs.PlateCarree())
    
    # Add map features with higher resolution for the zoomed-out view
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.STATES, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    
    # Define category colors
    category_colors = {
        1: 'green',
        2: 'yellow',
        3: 'orange',
        4: 'red',
        5: 'purple'
    }
    
    # Plot landfall points and labels
    for _, row in florida_df.iterrows():
        # Plot point
        ax.scatter(
            row['longitude'],
            row['latitude'],
            c=category_colors[row['category']],
            s=50,
            alpha=0.7,
            transform=ccrs.PlateCarree()
        )
        
        # Add label with smaller font to match baseline
        label = f"{row['name']} ({row['year']})"
        ax.text(
            row['longitude'],
            row['latitude'],
            label,
            fontsize=6,
            transform=ccrs.PlateCarree(),
            ha='center',
            va='center'
        )
    
    # Add title
    plt.title(
        "Baseline US Hurricane Landfalls (Cat 1-5), 1851-Present - Raw Labels",
        pad=20,
        fontsize=14
    )
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', 
                  markerfacecolor=color, label=f'Category {cat}',
                  markersize=8)
        for cat, color in category_colors.items()
    ]
    ax.legend(
        handles=legend_elements,
        loc='upper right',
        title='Hurricane Categories'
    )
    
    # Save the plot
    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches='tight',
        pad_inches=0.1
    )
    plt.close()

def main():
    """Main function to generate the South Florida map."""
    # Create output directory if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Define paths
    data_path = Path('data') / 'us_hurricane_landfalls_cat1_5.csv'
    output_path = output_dir / 'south_florida_landfalls.png'
    
    # Check if data exists
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        print("Please run parse_hurdat.py first to generate the data file.")
        return
    
    # Create the South Florida map
    print("Generating South Florida map...")
    create_south_florida_map(str(data_path), str(output_path))
    print(f"Saved South Florida map to {output_path}")

if __name__ == '__main__':
    main() 