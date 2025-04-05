#!/usr/bin/env python3
"""
Test Cluster Plotting Script (v0)

This script creates a map visualization of a small cluster of overlapping labels
for Phase 2 of the project.
"""

import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import sys

# Constants
PHASE2_OUTPUT_DIR = Path('output') / 'phase2'

def create_cluster_map(data_path: str, output_path: str) -> None:
    """
    Create a map of the test cluster with raw labels.
    
    Args:
        data_path: Path to the CSV file containing cluster data
        output_path: Path where to save the output PNG file
    """
    # Read the data
    df = pd.read_csv(data_path)
    
    # Create figure and axes - match South Florida map size
    plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent to match South Florida map (showing full East Coast context)
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
        
        # Add label with smaller font to match South Florida map
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
        "Test Cluster - Raw Labels (v0)",
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
    """Main function to generate the test cluster map."""
    # Create Phase 2 output directory if it doesn't exist
    PHASE2_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    # Define paths
    data_path = Path('data') / 'test_cluster_data.csv'
    output_path = PHASE2_OUTPUT_DIR / 'output_iteration_0.png'
    
    # Check if data exists
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        print("Please run extract_test_cluster.py first to generate the data file.")
        return
    
    # Create the test cluster map
    print("Generating test cluster map...")
    create_cluster_map(str(data_path), str(output_path))
    print(f"Saved test cluster map to {output_path}")

if __name__ == '__main__':
    main() 