#!/usr/bin/env python3
"""
Test script for hurricane clustering visualization.
This script tests different DBSCAN parameters and visualizes the resulting clusters
to help tune the clustering for continuous chains of hurricanes.
"""

import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path
from sklearn.cluster import DBSCAN
import numpy as np
from matplotlib.colors import rgb2hex
import colorsys

def generate_distinct_colors(n):
    """Generate n visually distinct colors."""
    colors = []
    for i in range(n):
        hue = i / n
        saturation = 0.9
        value = 0.9
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(rgb2hex(rgb))
    return colors

def coastline_metric(p1, p2):
    """
    Custom metric for DBSCAN that considers both direct distance and path continuity.
    
    Args:
        p1, p2: Points as [longitude, latitude]
        
    Returns:
        float: Distance metric between the points
    """
    lon1, lat1 = p1
    lon2, lat2 = p2
    
    # Calculate differences
    dlon = abs(lon1 - lon2)
    dlat = abs(lat1 - lat2)
    
    # Consider both the direct distance and the path angle
    direct_distance = np.sqrt(dlon**2 + dlat**2)
    
    # Calculate angle between points relative to horizontal
    # This helps identify natural breaks in hurricane paths
    angle = np.arctan2(dlat, dlon)
    angle_penalty = abs(np.sin(angle)) * 0.3  # Penalize sharp vertical changes
    
    return direct_distance + angle_penalty

def test_clustering(data_path: str, eps: float, min_samples: int) -> None:
    """
    Test clustering parameters and visualize results.
    
    Args:
        data_path: Path to the hurricane data CSV
        eps: DBSCAN epsilon parameter (maximum distance between points)
        min_samples: DBSCAN min_samples parameter
    """
    # Read all data without filtering
    df = pd.read_csv(data_path)
    
    # Extract coordinates for clustering
    coordinates = df[['longitude', 'latitude']].values
    
    # Perform clustering with custom metric
    clustering = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric=coastline_metric
    ).fit(coordinates)
    
    # Add cluster labels to dataframe
    df['cluster'] = clustering.labels_
    
    # Count clusters
    num_clusters = len(set(clustering.labels_[clustering.labels_ >= 0]))
    print(f"Number of clusters: {num_clusters}")
    print(f"Number of noise points: {sum(clustering.labels_ == -1)}")
    
    # Generate distinct colors for clusters
    colors = generate_distinct_colors(num_clusters + 1)
    
    # Create figure and axes
    fig = plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent
    ax.set_extent([-100, -60, 15, 50], crs=ccrs.PlateCarree())
    
    # Add map features
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.STATES, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue')
    
    # Plot points colored by cluster
    for cluster_id in range(-1, num_clusters):
        cluster_points = df[df['cluster'] == cluster_id]
        color = 'black' if cluster_id == -1 else colors[cluster_id]
        marker = 'x' if cluster_id == -1 else 'o'
        
        # Plot points with smaller size
        ax.scatter(
            cluster_points['longitude'],
            cluster_points['latitude'],
            c=[color],
            marker=marker,
            s=20,  # Even smaller points for better visibility with full dataset
            label=f'Cluster {cluster_id}' if cluster_id >= 0 else 'Noise',
            transform=ccrs.PlateCarree(),
            zorder=5
        )
        
        # Draw lines connecting points in the same cluster
        if cluster_id >= 0 and len(cluster_points) > 1:
            # Sort points by longitude to connect them in a reasonable order
            sorted_points = cluster_points.sort_values('longitude')
            lons = sorted_points['longitude'].values
            lats = sorted_points['latitude'].values
            
            ax.plot(
                lons,
                lats,
                color=color,
                linestyle='-',
                linewidth=0.5,
                alpha=0.3,
                transform=ccrs.PlateCarree(),
                zorder=4
            )
    
    # Add title with parameters
    plt.title(
        f"Hurricane Clustering Test\n"
        f"eps={eps}, min_samples={min_samples}, clusters={num_clusters}",
        fontsize=12
    )
    
    # Save plot
    output_dir = Path('output') / 'phase3_algo' / 'clustering_tests'
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / 'clustering_test.png'
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Saved clustering test plot to {output_path}")
    plt.close()

def main():
    """Test clustering parameters."""
    data_path = Path('data') / 'us_hurricane_landfalls_cat1_5.csv'
    
    # Test with a single set of parameters for iteration
    eps = 0.8  # Starting with a moderate epsilon
    min_samples = 2  # Requiring at least 2 points for a cluster
    
    print(f"\nTesting eps={eps}, min_samples={min_samples}")
    test_clustering(data_path, eps, min_samples)

if __name__ == "__main__":
    main() 