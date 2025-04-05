#!/usr/bin/env python3
"""
Baseline Hurricane Landfall Map Generator

This script creates a baseline map showing all US hurricane landfalls
with raw text labels placed directly at the landfall points.
"""

import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
from typing import Tuple

def create_baseline_map(data_path: str, output_path: str) -> None:
    """
    Create a baseline map of US hurricane landfalls with raw labels.
    
    Args:
        data_path: Path to the CSV file containing landfall data
        output_path: Path where to save the output PNG file
    """
    # Read the data
    df = pd.read_csv(data_path)
    
    # Create figure and axes
    plt.figure(figsize=(15, 10))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent (US East Coast, Gulf Coast, and Atlantic)
    ax.set_extent([-100, -60, 20, 50], crs=ccrs.PlateCarree())
    
    # Add map features
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
    for _, row in df.iterrows():
        # Plot point
        ax.scatter(
            row['longitude'],
            row['latitude'],
            c=category_colors[row['category']],
            s=50,
            alpha=0.7,
            transform=ccrs.PlateCarree()
        )
        
        # Add label
        label = f"{row['name']} ({row['year']})"
        ax.text(
            row['longitude'],
            row['latitude'],
            label,
            fontsize=8,
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
    """Main function to generate the baseline map."""
    # Create output directory if it doesn't exist
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Define paths
    data_path = Path('data') / 'us_hurricane_landfalls_cat1_5.csv'
    output_path = output_dir / 'baseline_us_cat1_5.png'
    
    # Check if data exists
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        print("Please run parse_hurdat.py first to generate the data file.")
        return
    
    # Create the baseline map
    print("Generating baseline map...")
    create_baseline_map(str(data_path), str(output_path))
    print(f"Saved baseline map to {output_path}")

if __name__ == '__main__':
    main() 