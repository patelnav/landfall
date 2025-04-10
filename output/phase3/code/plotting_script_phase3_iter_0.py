#!/usr/bin/env python3
"""
Florida Hurricane Landfall Map Generator - adjustText Focused Approach

This script creates a map of Florida hurricane landfalls, adding one cluster at a time
and using adjustText as the primary layout engine for label placement optimization.
"""

import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path
from sklearn.cluster import DBSCAN
from adjustText import adjust_text
import sys

def create_florida_map(data_path: str, output_path: str, iteration: int) -> None:
    """
    Create a map of Florida hurricane landfalls, adding one cluster per iteration.
    
    Args:
        data_path: Path to the CSV file containing landfall data
        output_path: Path where to save the output PNG file
        iteration: Current iteration number (determines how many clusters to show)
    """
    # Read the full data
    df = pd.read_csv(data_path)
    
    # Sort by category (higher categories first) and proximity to Florida
    df['miami_distance'] = ((df['longitude'] - (-80.2)) ** 2 + 
                          (df['latitude'] - 25.8) ** 2) ** 0.5
    df = df.sort_values(by=['category', 'miami_distance'], ascending=[False, True])
    
    # Define significant hurricanes to include (25 major hurricanes)
    significant_hurricanes = [
        "ANDREW (1992)",
        "MICHAEL (2018)",
        "KATRINA (2005)",
        "WILMA (2005)",
        "IRMA (2017)",
        "IAN (2022)",
        "CHARLEY (2004)",
        "DONNA (1960)",
        "ELOISE (1975)",
        "OPAL (1995)",
        "DENNIS (2005)",
        "JEANNE (2004)",
        "FRANCES (2004)",
        "DORIAN (2019)",
        "EASY (1950)",
        "BETSY (1965)",
        "IRENE (1999)",
        "KING (1950)",
        "GEORGES (1998)",
        "ELENA (1985)",
        "KATE (1985)",
        "FLOYD (1999)",
        "DAVID (1979)",
        "HUGO (1989)",
        "CAMILLE (1969)"
    ]
    
    # Filter to include these hurricanes
    plot_df = df[df.apply(lambda row: f"{row['name']} ({row['year']})" in significant_hurricanes, axis=1)]
    
    # Extract coordinates for clustering
    coordinates = plot_df[['longitude', 'latitude']].values
    
    # Perform clustering using DBSCAN
    # epsilon: maximum distance between points to be considered in the same cluster
    # min_samples: minimum number of points to form a cluster
    clustering = DBSCAN(eps=3.0, min_samples=1).fit(coordinates)
    
    # Add cluster labels to the dataframe
    plot_df['cluster'] = clustering.labels_
    
    # Count number of clusters
    num_clusters = len(set(clustering.labels_))
    print(f"Total clusters: {num_clusters}")
    
    # Sort clusters by significance (average category) to process more significant clusters first
    cluster_info = []
    for cluster_id in range(num_clusters):
        cluster_df = plot_df[plot_df['cluster'] == cluster_id]
        avg_category = cluster_df['category'].mean()
        min_distance = cluster_df['miami_distance'].min()
        cluster_info.append((cluster_id, avg_category, min_distance, len(cluster_df)))
    
    # Sort by average category (descending), then by distance to Miami (ascending)
    cluster_info.sort(key=lambda x: (-x[1], x[2]))
    
    # Create figure and axes
    plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent to match baseline (showing full East Coast context)
    # Modify to extend further south to ensure Florida and Gulf are fully visible
    ax.set_extent([-100, -60, 15, 50], crs=ccrs.PlateCarree())
    
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
    
    # Determine how many clusters to display based on iteration
    # For iteration 0, display 1 cluster; for iteration 1, display 2 clusters, etc.
    clusters_to_display = min(iteration + 1, num_clusters)
    
    # Plot landfall points and labels for the selected clusters
    all_texts = []
    for i in range(clusters_to_display):
        cluster_id, _, _, _ = cluster_info[i]
        cluster_df = plot_df[plot_df['cluster'] == cluster_id]
        
        # Plot each point in the cluster
        for _, row in cluster_df.iterrows():
            # Get coordinates and label
            point_x, point_y = row['longitude'], row['latitude']
            label = f"{row['name']} ({row['year']})"
            
            # Plot the hurricane point
            ax.scatter(
                point_x, 
                point_y,
                c=category_colors[row['category']],
                s=50,
                transform=ccrs.PlateCarree(),
                zorder=5
            )
            
            # Add text label with a small offset from the point
            small_offset_x, small_offset_y = 0.1, 0.1
            text = ax.text(
                point_x + small_offset_x,
                point_y + small_offset_y,
                label,
                fontsize=8,
                transform=ccrs.PlateCarree(),
                zorder=10
            )
            all_texts.append(text)
    
    # Add title
    plt.title(
        f"US Hurricane Landfalls (Cat 1-5), 1851-Present - Iteration {iteration}\n"
        f"Displaying {clusters_to_display} of {num_clusters} clusters",
        fontsize=12
    )
    
    # Add legend for hurricane categories
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
    
    # Add iteration number to bottom right corner
    ax.text(
        0.98, 0.02,
        f"Iteration: {iteration}",
        transform=ax.transAxes,
        fontsize=8,
        ha='right',
        bbox=dict(facecolor='white', alpha=0.7, boxstyle="round,pad=0.3")
    )
    
    # Use adjustText to adjust the text positions and avoid overlaps
    # Configure with parameters that give adjustText more freedom to place labels
    adjust_text(
        all_texts,
        arrowprops=dict(arrowstyle='->', color='gray', lw=0.5),
        expand_points=(1.2, 1.2),
        expand_text=(1.2, 1.2),
        force_points=(0.5, 0.5),
        force_text=(0.5, 0.5), 
        autoalign=True,  # Allow adjustText to align labels
    )
    
    # Save the plot
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Saved hurricane map to {output_path}")
    plt.close()

def main():
    """Main function to generate the map."""
    # Get iteration from command line args
    iteration = 0
    if len(sys.argv) > 1:
        try:
            iteration = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid iteration number '{sys.argv[1]}'")
            return

    # Define paths
    data_path = Path('data') / 'us_hurricane_landfalls_cat1_5.csv'
    output_path = Path('output') / 'phase3' / 'images' / f'florida_iter_{iteration}.png'
    
    # Check if data exists
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return
    
    # Create the map
    print(f"Generating hurricane map for iteration {iteration}...")
    create_florida_map(str(data_path), str(output_path), iteration)
    print(f"Saved hurricane map to {output_path}")

if __name__ == "__main__":
    main() 