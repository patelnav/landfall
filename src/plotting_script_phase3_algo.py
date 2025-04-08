#!/usr/bin/env python3
"""
Florida Hurricane Landfall Map Generator - Algorithmic Approach

This script creates a map of Florida hurricane landfalls using a structured polygon placement
algorithm to optimize label placement and avoid overlaps.
"""

import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path
from sklearn.cluster import DBSCAN
import sys
import shapely.geometry as geometry
from shapely import affinity
from shapely.ops import unary_union
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
from matplotlib import colors
import matplotlib.path as mpath
import pickle
import os
import random

# Add a constant for the placement cache
PLACEMENT_CACHE_PATH = Path('output') / 'phase3_algo' / 'placement_cache.pkl'

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

def create_label_text_polygon(x, y, text_list, font_size=6, char_width=0.05, line_height=0.3):
    """
    Create a precise polygon representing the text region.
    
    Args:
        x: X coordinate of the text start
        y: Y coordinate of the text start
        text_list: List of text strings
        font_size: Font size
        char_width: Width per character
        line_height: Height per line
        
    Returns:
        Polygon: A polygon representing the text
    """
    # Calculate box dimensions
    max_len = max(len(text) for text in text_list)
    box_width = max_len * char_width
    box_height = len(text_list) * line_height
    
    # Create text polygon (rectangle)
    text_box = geometry.box(
        x, 
        y, 
        x + box_width, 
        y + box_height
    )
    
    # Buffer it for safety
    return text_box.buffer(0.2)

def create_full_cluster_polygon(points, text_box_corners):
    """
    Create a polygon that encompasses both the text box and all cluster points.
    The approach is optimized to avoid excessively large areas.
    
    Args:
        points: Array of point coordinates for the cluster
        text_box_corners: Array of the four corners of the text box [(min_x,min_y), (max_x,min_y), etc.]
        
    Returns:
        Polygon: A polygon connecting the text box with all points
    """
    # Create a list to hold all vertices of the polygon
    vertices = []
    
    # Add the text box corners to the vertices
    vertices.extend(text_box_corners)
    
    # Calculate centroid of points
    if len(points) > 0:
        centroid_x = np.mean(points[:, 0])
        centroid_y = np.mean(points[:, 1])
        
        # Add the centroid (this helps create a more compact hull)
        vertices.append((centroid_x, centroid_y))
    
    # Add each point in the cluster
    for point in points:
        vertices.append(tuple(point))
        
    # Generate the convex hull of all vertices
    if len(vertices) >= 3:  # Need at least 3 points for a polygon
        hull = geometry.MultiPoint(vertices).convex_hull
        return hull
    else:
        # Fallback if not enough points
        return geometry.Polygon(vertices)

def calculate_text_dimensions(text_list, char_width=0.3, line_height=0.35):
    """
    Calculate dimensions of text box.
    
    Args:
        text_list: List of text strings
        char_width: Width per character (reduced for smaller text footprint)
        line_height: Height per line (reduced for tighter spacing)
        
    Returns:
        tuple: (width, height) of the text box
    """
    max_len = max(len(text) for text in text_list)
    width = max_len * char_width
    height = len(text_list) * line_height
    return width, height

def polygon_distance(poly1, poly2):
    """
    Calculate minimum distance between two polygons.
    
    Args:
        poly1, poly2: Shapely polygons
        
    Returns:
        float: Minimum distance between polygons
    """
    if poly1.intersects(poly2):
        return 0
    return poly1.distance(poly2)

def move_polygon(polygon, dx, dy):
    """
    Move a shapely polygon by the given offsets.
    
    Args:
        polygon: Shapely polygon
        dx, dy: Distance to move in x and y directions
        
    Returns:
        Polygon: Moved polygon
    """
    return affinity.translate(polygon, xoff=dx, yoff=dy)

def create_florida_map(data_path: str, output_path: str, iteration: int) -> None:
    """
    Create a map of Florida hurricane landfalls using a structured polygon placement algorithm.
    
    Args:
        data_path: Path to the CSV file containing landfall data
        output_path: Path where to save the output PNG file
        iteration: Number of clusters to display (1-based)
    """
    # Read the full data without filtering
    df = pd.read_csv(data_path)
    
    # Sort by category (higher categories first) and proximity to Florida
    df['miami_distance'] = ((df['longitude'] - (-80.2)) ** 2 + 
                          (df['latitude'] - 25.8) ** 2) ** 0.5
    df = df.sort_values(by=['category', 'miami_distance'], ascending=[False, True])
    
    # Extract coordinates for clustering
    coordinates = df[['longitude', 'latitude']].values
    
    # Perform clustering using DBSCAN with our custom metric
    clustering = DBSCAN(
        eps=0.8,  # Moderate epsilon for natural grouping
        min_samples=2,  # Require at least 2 points for a cluster
        metric=coastline_metric
    ).fit(coordinates)
    
    # Add cluster labels to the dataframe
    df['cluster'] = clustering.labels_
    
    # Count number of clusters
    num_clusters = len(set(clustering.labels_[clustering.labels_ >= 0]))
    print(f"Total clusters: {num_clusters}")
    
    # Sort clusters by significance (average category) to process more significant clusters first
    cluster_info = []
    for cluster_id in range(num_clusters):
        cluster_df = df[df['cluster'] == cluster_id]
        avg_category = cluster_df['category'].mean()
        min_distance = cluster_df['miami_distance'].min()
        cluster_info.append((cluster_id, avg_category, min_distance, len(cluster_df)))
    
    # Sort by average category (descending), then by distance to Miami (ascending)
    cluster_info.sort(key=lambda x: (-x[1], x[2]))
    
    # Number of clusters to display (ensure we don't exceed available clusters)
    clusters_to_display = min(iteration, num_clusters)
    if clusters_to_display <= 0:
        clusters_to_display = 1  # Show at least one cluster
    
    # Create figure and axes
    plt.figure(figsize=(15, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Set map extent to show more of the Caribbean and Atlantic
    ax.set_extent([-100, -50, 10, 45], crs=ccrs.PlateCarree())
    
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
    
    # Store cluster data for layout optimization
    cluster_data = []
    
    # PHASE 1: Collect all cluster data and create point-based polygons first
    for i in range(clusters_to_display):
        cluster_id, _, _, _ = cluster_info[i]
        cluster_df = df[df['cluster'] == cluster_id]
        
        # Get points for this cluster
        points = cluster_df[['longitude', 'latitude']].values
        
        # Calculate cluster centroid
        centroid_x = np.mean(points[:, 0])
        centroid_y = np.mean(points[:, 1])
        
        # Prepare labels
        labels = []
        for _, row in cluster_df.iterrows():
            label = f"{row['name']} ({row['year']})"
            labels.append(label)
        
        # Calculate text dimensions
        box_width, box_height = calculate_text_dimensions(labels)
        
        # Get initial target position for the label box
        target_x, target_y = get_initial_label_box_position(centroid_x, centroid_y, box_width, box_height)
        
        # Create a convex hull just for the landfall points
        points_hull = None
        if len(points) >= 3:
            # Add a small buffer to make sure all points are fully enclosed
            points_hull = geometry.MultiPoint(points).convex_hull.buffer(0.2)
        elif len(points) == 2:
            # Create a buffered line for 2 points
            points_hull = geometry.LineString(points).buffer(0.3)  # Increased buffer
        elif len(points) == 1:
            # Create a circular buffer for a single point
            points_hull = geometry.Point(points[0]).buffer(0.3)  # Increased buffer
        
        # For debugging, save the points coordinates for this cluster
        print(f"Cluster {cluster_id} points: {points.tolist()}")
        
        # Add to cluster data
        cluster_data.append({
            'id': cluster_id,
            'df': cluster_df,
            'points': points,
            'centroid': (centroid_x, centroid_y),
            'labels': labels,
            'box_dims': (box_width, box_height),
            'initial_pos': (target_x, target_y),
            'final_pos': (target_x, target_y),  # Will be updated during layout
            'text_polygon': None,  # Will be set during layout
            'points_hull': points_hull,  # Convex hull of just the points
            'full_polygon': points_hull,  # Initially just the points hull, will be extended with the label
        })
    
    # PHASE 2: Layout optimization - extend point hulls with labels
    placed_clusters = []
    placed_point_hulls = []  # Keep track of point hulls separately
    
    # First, ensure that point hulls don't overlap with each other
    # This is a preprocessing step to check if clusters need special handling
    overlapping_clusters = set()
    for i in range(len(cluster_data)):
        for j in range(i + 1, len(cluster_data)):
            hull_i = cluster_data[i]['points_hull']
            hull_j = cluster_data[j]['points_hull']
            if hull_i is not None and hull_j is not None and hull_i.intersects(hull_j):
                # Record these clusters as having overlapping point hulls
                overlapping_clusters.add(cluster_data[i]['id'])
                overlapping_clusters.add(cluster_data[j]['id'])
                print(f"Warning: Clusters {cluster_data[i]['id']} and {cluster_data[j]['id']} have overlapping landfall points")
    
    # Store all point hulls first
    for cluster in cluster_data:
        if cluster['points_hull'] is not None:
            placed_point_hulls.append(cluster['points_hull'])

    # Process each cluster
    for cluster_info in cluster_data:
        # Create initial text polygon
        target_x, target_y = cluster_info['initial_pos']
        box_width, box_height = cluster_info['box_dims']
        labels = cluster_info['labels']
        points = cluster_info['points']
        points_hull = cluster_info['points_hull']
        cluster_id = cluster_info['id']
        
        # Create text box corners for the initial position
        text_box_corners = [
            (target_x, target_y),  # Bottom-left
            (target_x + box_width, target_y),  # Bottom-right
            (target_x + box_width, target_y + box_height),  # Top-right
            (target_x, target_y + box_height),  # Top-left
        ]
        
        # Create a polygon for the text box
        text_box = geometry.box(target_x, target_y, target_x + box_width, target_y + box_height)
        text_polygon = text_box.buffer(0.2)  # Add a small buffer
        
        # Check if the text box collides with ANY point hull (not just this cluster's)
        has_collision = False
        
        # First, check if the text polygon intersects with any other point hull
        for other_hull in placed_point_hulls:
            if text_polygon.intersects(other_hull) and other_hull != points_hull:
                has_collision = True
                break
        
        # Then check if it intersects with any already placed cluster's full polygon
        if not has_collision:
            for placed in placed_clusters:
                if text_polygon.intersects(placed['full_polygon']):
                    has_collision = True
                    break
        
        # If collision, find new position
        if has_collision:
            print(f"Collision for cluster {cluster_info['id']}, repositioning...")
            
            # Try different positions with increasing distances
            best_pos = None
            min_overlap_area = float('inf')
            
            # Define search parameters
            angles = np.linspace(0, 2*np.pi, 36)  # Every 10 degrees
            distances = np.linspace(1, 20, 20)  # Increased max distance
            
            for distance in distances:
                for angle in angles:
                    # Calculate new position
                    new_x = target_x + distance * np.cos(angle)
                    new_y = target_y + distance * np.sin(angle)
                    
                    # Create new text box
                    new_text_box = geometry.box(
                        new_x, new_y, 
                        new_x + box_width, new_y + box_height
                    )
                    new_text_polygon = new_text_box.buffer(0.2)
                    
                    # Check for collisions with point hulls
                    text_collides_with_other_points = False
                    for other_hull in placed_point_hulls:
                        if new_text_polygon.intersects(other_hull) and other_hull != points_hull:
                            text_collides_with_other_points = True
                            break
                    
                    # Skip this position if it collides with other point hulls
                    if text_collides_with_other_points:
                        continue
                    
                    # Create new full polygon by combining the fixed points hull with the new text box
                    new_full_polygon = None
                    if points_hull is not None:
                        new_full_polygon = unary_union([points_hull, new_text_polygon])
                    else:
                        new_full_polygon = new_text_polygon
                    
                    # Check overlap with placed clusters using full polygons
                    total_overlap = 0
                    for placed in placed_clusters:
                        if new_full_polygon.intersects(placed['full_polygon']):
                            intersection = new_full_polygon.intersection(placed['full_polygon'])
                            total_overlap += intersection.area
                    
                    # Update best position if better
                    if total_overlap < min_overlap_area:
                        min_overlap_area = total_overlap
                        best_pos = (new_x, new_y)
                        
                    # If no overlap, use this position
                    if total_overlap == 0:
                        break
                
                # If found position with no overlap, stop
                if min_overlap_area == 0:
                    break
            
            # Use best position found
            if best_pos:
                target_x, target_y = best_pos
                
                # Create updated text box
                text_box = geometry.box(
                    target_x, target_y, 
                    target_x + box_width, target_y + box_height
                )
                text_polygon = text_box.buffer(0.2)
                
                # Update full polygon
                if points_hull is not None:
                    full_polygon = unary_union([points_hull, text_polygon])
                else:
                    full_polygon = text_polygon
                
                print(f"  Found better position at ({target_x:.2f}, {target_y:.2f})")
            else:
                print(f"  Warning: Could not find non-colliding position")
                # As a last resort, move it far away
                target_x += 15  # Increased offset
                target_y -= 8   # Increased offset
                
                # Create updated text box
                text_box = geometry.box(
                    target_x, target_y, 
                    target_x + box_width, target_y + box_height
                )
                text_polygon = text_box.buffer(0.2)
                
                # Update full polygon
                if points_hull is not None:
                    full_polygon = unary_union([points_hull, text_polygon])
                else:
                    full_polygon = text_polygon
        else:
            # Create the full polygon by combining the points hull and the text box
            full_polygon = None
            if points_hull is not None:
                # Use a union operation if we have a points hull
                full_polygon = unary_union([points_hull, text_polygon])
            else:
                # Just use the text polygon if there's no points hull
                full_polygon = text_polygon
        
        # Update cluster info with final position and polygons
        cluster_info['final_pos'] = (target_x, target_y)
        cluster_info['text_polygon'] = text_polygon
        cluster_info['full_polygon'] = full_polygon
        
        # Add to placed clusters
        placed_clusters.append(cluster_info)
    
    # Now render all clusters
    for cluster_info in cluster_data:
        final_x, final_y = cluster_info['final_pos']
        box_width, box_height = cluster_info['box_dims']
        labels = cluster_info['labels']
        points = cluster_info['points']
        cluster_df = cluster_info['df']
        points_hull = cluster_info['points_hull']
        full_polygon = cluster_info['full_polygon']
        
        # Find the bounds of the text box
        text_box_min_x = final_x
        text_box_max_x = final_x + box_width
        text_box_min_y = final_y
        text_box_max_y = final_y + box_height
        
        # Draw connecting lines if more than one point
        if len(points) > 1:
            # Sort points by longitude to connect them in a reasonable order
            sorted_df = cluster_df.sort_values('longitude')
            lons = sorted_df['longitude'].values
            lats = sorted_df['latitude'].values
            
            # Draw lines connecting points in the cluster
            ax.plot(
                lons,
                lats,
                color='gray',
                linestyle='-',
                linewidth=0.5,
                alpha=0.3,
                transform=ccrs.PlateCarree(),
                zorder=4
            )
        
        # Draw the label box border (no fill)
        rectangle = patches.Rectangle(
            (text_box_min_x, text_box_min_y),
            box_width,
            box_height,
            edgecolor='black',
            facecolor='none',
            linewidth=0.5,
            transform=ccrs.PlateCarree(),
            zorder=6
        )
        ax.add_patch(rectangle)
        
        # Draw the points hull in green (just the landfall points)
        if points_hull is not None and hasattr(points_hull, 'exterior'):
            points_path = mpath.Path(np.array(points_hull.exterior.coords))
            points_patch = patches.PathPatch(
                points_path,
                facecolor='none',
                edgecolor='green',
                linewidth=0.5,
                alpha=0.7,
                transform=ccrs.PlateCarree(),
                zorder=3
            )
            ax.add_patch(points_patch)
        
        # Draw the full polygon outline in blue (points + text box)
        if hasattr(full_polygon, 'exterior'):
            poly_path = mpath.Path(np.array(full_polygon.exterior.coords))
            poly_patch = patches.PathPatch(
                poly_path,
                facecolor='none',
                edgecolor='blue',
                linewidth=0.8,
                alpha=0.7,
                transform=ccrs.PlateCarree(),
                zorder=4
            )
            ax.add_patch(poly_patch)
        
        # Draw direct connections from each landfall point to its corresponding category dot
        # Track points that have been connected to avoid duplicate lines
        connected_points = set()
        
        # Sort rows by latitude (north to south) to prevent line crossings
        sorted_rows = []
        for idx, row in cluster_df.iterrows():
            sorted_rows.append((idx, row))
        
        # Sort by latitude (descending, so north to south)
        sorted_rows.sort(key=lambda x: x[1]['latitude'], reverse=True)
        
        # Draw category-colored dots and labels within the box
        line_height = 0.35  # Reduced line height 
        dot_offset = 0.4  # Keep category dots INSIDE the text box
        label_offset = 0.5  # Reduced offset for label text from dot (was 1.0)
        
        for j, (idx, row) in enumerate(sorted_rows):
            text_y = final_y + box_height - (j + 0.5) * line_height
            point_x, point_y = row['longitude'], row['latitude']
            
            # Place the category dot INSIDE the text box
            dot_x = text_box_min_x + dot_offset
            
            # Add the colored category dot inside the text box
            ax.text(
                dot_x,
                text_y,
                "●",  # Unicode bullet point
                fontsize=5,  # Reduced font size
                color=category_colors[row['category']],
                transform=ccrs.PlateCarree(),
                zorder=10,
                va='center',
                ha='left'
            )
            
            # Add the hurricane name and year after the dot (inside the box)
            ax.text(
                dot_x + label_offset,
                text_y,
                f"{row['name']} ({row['year']})",
                fontsize=5,  # Reduced font size
                transform=ccrs.PlateCarree(),
                zorder=10,
                va='center',
                ha='left'
            )
            
            # Draw a connection line from the landfall point to its category dot
            # We use a unique key for each point to avoid duplicate lines
            point_key = (point_x, point_y)
            if point_key not in connected_points:
                ax.plot(
                    [point_x, dot_x],
                    [point_y, text_y],
                    color='black',
                    linestyle='-',
                    linewidth=0.3,  # Thin line width
                    alpha=0.6,      # Added transparency
                    transform=ccrs.PlateCarree(),
                    zorder=5
                )
                connected_points.add(point_key)
        
        # Draw the hurricane points
        ax.scatter(
            points[:, 0], 
            points[:, 1],
            c='black',
            s=10,  # Further reduced size for less overlap
            transform=ccrs.PlateCarree(),
            zorder=5
        )
    
    # Add title
    plt.title(
        f"US Hurricane Landfalls (Cat 1-5), 1851-Present - Algorithmic Approach\n"
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
        f"Clusters shown: {clusters_to_display}",
        transform=ax.transAxes,
        fontsize=8,
        ha='right',
        bbox=dict(facecolor='white', alpha=0.7, boxstyle="round,pad=0.3")
    )
    
    # Save the plot
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    print(f"Saved hurricane map to {output_path}")
    plt.close()

def get_initial_label_box_position(centroid_x: float, centroid_y: float, 
                                  box_width: float, box_height: float) -> tuple:
    """
    Determine the initial target position for a label box based on cluster centroid.
    
    Args:
        centroid_x: X coordinate of the cluster centroid
        centroid_y: Y coordinate of the cluster centroid
        box_width: Width of the label box
        box_height: Height of the label box
        
    Returns:
        tuple: (target_x, target_y) coordinates for the label box
    """
    # Default offset from centroid - increased for more space between landfall dots and labels
    offset_x = 4.0  # Further increased for more distance between landfall dots and label box
    offset_y = 0.0
    
    # Adjust offset based on centroid location
    if centroid_x > -81:  # East Florida
        offset_x = 5.0  # Further increased offset
    elif centroid_x < -85:  # West Florida
        offset_x = 3.5  # Further increased offset
    
    if centroid_y < 27:  # South Florida
        offset_y = 2.0  # Further increased offset
    elif centroid_y > 30:  # North Florida
        offset_y = -2.0  # Further increased offset
    
    # Calculate target position
    target_x = centroid_x + offset_x
    target_y = centroid_y + offset_y
    
    # Adjust to account for box dimensions (place at bottom-left corner)
    target_x -= box_width / 2
    target_y -= box_height / 2
    
    return target_x, target_y

def find_closest_point_on_box(point, min_x, max_x, min_y, max_y):
    """
    Find the closest point on a box boundary to a given point.
    
    Args:
        point: Point as [x, y]
        min_x, max_x, min_y, max_y: Box boundary coordinates
        
    Returns:
        tuple: (x, y) of closest point on box boundary
    """
    px, py = point
    
    # Calculate distances to each edge of the box
    dist_left = abs(px - min_x)
    dist_right = abs(px - max_x)
    dist_bottom = abs(py - min_y)
    dist_top = abs(py - max_y)
    
    # Find the minimum distance
    min_dist = min(dist_left, dist_right, dist_bottom, dist_top)
    
    # Return the closest point on the box boundary
    if min_dist == dist_left:
        return min_x, max(min_y, min(max_y, py))
    elif min_dist == dist_right:
        return max_x, max(min_y, min(max_y, py))
    elif min_dist == dist_bottom:
        return max(min_x, min(max_x, px)), min_y
    else:  # dist_top
        return max(min_x, min(max_x, px)), max_y

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

    # Set random seed for reproducibility
    random.seed(42)

    # Define paths
    data_path = Path('data') / 'us_hurricane_landfalls_cat1_5.csv'
    output_dir = Path('output') / 'phase3_algo' / 'images'
    output_path = output_dir / f'florida_algo_iter_{iteration}.png'
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
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