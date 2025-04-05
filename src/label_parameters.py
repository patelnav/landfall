#!/usr/bin/env python3
"""
Label Parameters for Hurricane Landfall Map

This file contains parameters and functions for label placement
that will be modified by the LLM during Phase 3.
"""

from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt
from adjustText import adjust_text
import numpy as np


def define_clusters() -> Dict[str, Dict[str, Any]]:
    """
    Define clusters of hurricane labels that should be grouped together.
    Each cluster can have its own adjustText parameters and positioning.

    Returns:
        dict: Dictionary of cluster definitions with parameters
    """
    # Define clusters of hurricane labels by region (focus on 25 major hurricanes)
    return {
        "south_florida": {
            "labels": [
                "ANDREW (1992)",
                "KATRINA (2005)",
                "WILMA (2005)",
                "IRENE (1999)",
                "BETSY (1965)",
                "KING (1950)",
                "GEORGES (1998)"
            ],
            "position": {
                "x_offset": 1.3,  # Slightly increased x_offset again
                "y_offset": -0.3 # Slightly moved down further
            },
            "adjust_params": {
                "force_points": (2.0, 2.0),
                "force_text": (3.0, 3.0),
                "expand_points": (1.8, 1.8),
                "precision": 0.05,
                "lim": 300
            },
            "layout": "arc"
        },
        
        "east_coast": {
            "labels": [
                "JEANNE (2004)",
                "FRANCES (2004)",
                "DORIAN (2019)",
                "DAVID (1979)",
                "FLOYD (1999)",
                "HUGO (1989)"
            ],
            "position": {
                "x_offset": 1.8, # Increased x_offset further right
                "y_offset": 0.4  # Slight y_offset to move up a bit more
            },
            "adjust_params": {
                "force_points": (1.5, 1.5),
                "force_text": (2.5, 2.5),
                "expand_points": (1.5, 1.5),
                "precision": 0.05,
                "lim": 300
            },
            "layout": "column" # Keep column for now
        },
        
        "central_florida": {
            "labels": [
                "CHARLEY (2004)",
                "IRMA (2017)",
                "IAN (2022)",
                "DONNA (1960)"
            ],
            "position": {
                "x_offset": 0.0,
                "y_offset": -1.2 # Increased y_offset to move further down
            },
            "adjust_params": {
                "force_points": (2.0, 2.0),
                "force_text": (3.0, 3.0),
                "expand_points": (1.8, 1.8),
                "precision": 0.05,
                "lim": 300
            },
            "layout": "grid"
        },
        
        "panhandle": {
            "labels": [
                "MICHAEL (2018)",
                "EASY (1950)",
                "ELOISE (1975)",
                "OPAL (1995)",
                "DENNIS (2005)",
                "ELENA (1985)",
                "KATE (1985)",
                "CAMILLE (1969)"
            ],
            "position": {
                "x_offset": -0.4, # Slightly to the left more
                "y_offset": 0.9 # Move up a bit more
            },
            "adjust_params": {
                "force_points": (1.5, 1.5),
                "force_text": (2.0, 2.0),
                "expand_points": (1.5, 1.5),
                "precision": 0.05,
                "lim": 300
            },
            "layout": "row"
        }
    }


def apply_cluster_layout(texts: List, points: List[Tuple[float, float]],
                         cluster_name: str, cluster_data: Dict[str, Any]) -> List:
    """
    Apply a specific layout pattern to a cluster of labels.

    Args:
        texts: List of text objects in the cluster
        points: List of (x,y) coordinate tuples for the corresponding points
        cluster_name: Name of the cluster
        cluster_data: Cluster definition data

    Returns:
        List: Updated text objects with the layout applied
    """
    layout_type = cluster_data.get("layout", "default")

    if layout_type == "arc":
        # Create an arc layout around a center point
        center_x = sum(p[0] for p in points) / len(points)
        center_y = sum(p[1] for p in points) / len(points)
        radius = 3.2  # Adjusted radius for arc layout (increased from 3.0 to 3.2)

        # Calculate positions in an arc
        for i, text in enumerate(texts):
            angle = np.pi * 0.5 + (np.pi / (len(texts) + 1)) * (i + 1)
            x = center_x + radius * np.cos(angle)
            y = center_y + radius * np.sin(angle)
            text.set_position((x, y))

    elif layout_type == "row":
        # Arrange labels in a horizontal row
        start_x = min(p[0] for p in points) - 0.5
        y = sum(p[1] for p in points) / len(points) + 1.5 # Adjusted y position (increased)
        spacing = 1.7  # Adjusted horizontal spacing factor (increased)

        for i, text in enumerate(texts):
            text.set_position((start_x + i * spacing, y))

    elif layout_type == "column":
        # Arrange labels in a vertical column
        x = sum(p[0] for p in points) / len(points) + 1.6 # Adjusted x position (increased)
        start_y = min(p[1] for p in points) - 0.5
        spacing = 1.0  # Adjusted vertical spacing factor (increased)

        for i, text in enumerate(texts):
            text.set_position((x, start_y + i * spacing))

    elif layout_type == "grid":
        # Arrange labels in a grid pattern
        start_x = min(p[0] for p in points) - 1.0 # Adjusted start x (increased)
        start_y = min(p[1] for p in points) - 1.0 # Adjusted start y (increased)
        cols = int(np.ceil(np.sqrt(len(texts))))
        spacing_x = 1.7 # Adjusted spacing x (increased)
        spacing_y = 1.0 # Adjusted spacing y (increased)

        for i, text in enumerate(texts):
            row = i // cols
            col = i % cols
            text.set_position((start_x + col * spacing_x, start_y + row * spacing_y))

    return texts


def cluster_labels(texts: List, points_data: Dict[str, Tuple[float, float]]) -> Dict[str, List]:
    """
    Process label clusters and apply cluster-specific adjustments.

    Args:
        texts: List of all text objects
        points_data: Dictionary mapping label text to (x,y) coordinates

    Returns:
        dict: Dictionary with cluster names as keys and processed text objects as values
    """
    # Get cluster definitions
    clusters = define_clusters()

    # Dictionary to store texts by cluster
    clustered_texts = {}
    clustered_points = {}
    used_labels = set()

    # Group texts by their clusters
    for cluster_name, cluster_data in clusters.items():
        cluster_labels = cluster_data.get("labels", [])
        clustered_texts[cluster_name] = []
        clustered_points[cluster_name] = []

        # Find text objects that belong to this cluster
        for text in texts:
            label = text.get_text()
            if label in cluster_labels:
                clustered_texts[cluster_name].append(text)
                clustered_points[cluster_name].append(points_data[label])
                used_labels.add(label)

    # Add a default cluster for all unclustered texts
    unclustered_texts = [text for text in texts if text.get_text() not in used_labels]
    if unclustered_texts:
        clustered_texts["unclustered"] = unclustered_texts
        clustered_points["unclustered"] = [points_data[text.get_text()] for text in unclustered_texts]

    # Apply layout patterns and offsets to each cluster
    for cluster_name, cluster_data in clusters.items():
        if cluster_name in clustered_texts and clustered_texts[cluster_name]:
            # Apply the layout pattern if specified
            if "layout" in cluster_data:
                clustered_texts[cluster_name] = apply_cluster_layout(
                    clustered_texts[cluster_name],
                    clustered_points[cluster_name],
                    cluster_name,
                    cluster_data
                )

            # Apply global cluster offset if specified
            if "position" in cluster_data:
                x_offset = cluster_data["position"].get("x_offset", 0)
                y_offset = cluster_data["position"].get("y_offset", 0)

                for text in clustered_texts[cluster_name]:
                    current_pos = text.get_position()
                    text.set_position((current_pos[0] + x_offset, current_pos[1] + y_offset))

    return clustered_texts, clustered_points


def apply_label_adjustments(texts: List, ax: plt.Axes) -> None:
    """
    Apply adjustText to optimize label placement, with cluster-aware processing.

    Args:
        texts: List of text objects to adjust
        ax: Matplotlib axes object
    """
    # Create a dictionary mapping label text to point coordinates
    points_data = {}
    for text in texts:
        # Get the original position (should be the hurricane landfall point)
        points_data[text.get_text()] = text.get_position()

    # Process clusters
    clustered_texts, clustered_points = cluster_labels(texts, points_data)

    # Apply adjustText to each cluster with cluster-specific parameters
    clusters = define_clusters()

    # Process defined clusters first
    for cluster_name, cluster_texts in clustered_texts.items():
        if not cluster_texts:
            continue

        # Skip if the cluster has manual layout only (no adjustText)
        if cluster_name in clusters and clusters[cluster_name].get("skip_adjust", False):
            continue

        # Get cluster-specific adjustText parameters
        if cluster_name in clusters and "adjust_params" in clusters[cluster_name]:
            params = clusters[cluster_name]["adjust_params"]

            # Apply adjustText with cluster-specific parameters
            adjust_text(
                cluster_texts,
                ax=ax,
                arrowprops=dict(arrowstyle='-', color='grey', lw=0.5),
                expand_points=params.get("expand_points", (1.8, 1.8)),
                force_points=params.get("force_points", (2.0, 2.0)),
                force_text=params.get("force_text", (3.0, 3.0)),
                precision=params.get("precision", 0.05),
                autoalign='xy',
                only_move={'points':'xy', 'text':'xy'},
                lim=params.get("lim", 500),
                avoid_self=True,
                avoid_text_characters=False
            )
        else:
            # Use default parameters for unclustered or clusters without specific params
            adjust_text(
                cluster_texts,
                ax=ax,
                arrowprops=dict(arrowstyle='-', color='grey', lw=0.5),
                expand_points=(1.8, 1.8),      # Reasonable expansion
                force_points=(2.0, 2.0),       # Moderate force from points
                force_text=(3.0, 3.0),         # Moderate force between texts
                precision=0.05,                # Standard precision
                autoalign='xy',                # Keep autoalign
                only_move={'points':'xy', 'text':'xy'},
                lim=500,                       # Reasonable limit
                avoid_self=True,               # Keep avoid_self
                avoid_text_characters=False    # Turn off character avoidance
            )


def get_manual_adjustments() -> Dict[str, Dict[str, Any]]:
    """
    Return manual adjustments for specific hurricane labels.
    This function will be modified by the LLM to override problematic
    label positions that adjustText doesn't handle well.

    Returns:
        dict: Dictionary with hurricane identifiers as keys and 
              adjustment parameters as values
    """
    # Manual adjustments for individual labels (applied after clustering)
    return {
        # Examples of manual adjustments for specific hurricanes
        "ANDREW (1992)": {
            "x_offset": 0.9, # Adjusted x_offset further right
            "y_offset": -0.6, # Adjusted y_offset further down
            "fontsize": 8.0
        },
        "MICHAEL (2018)": {
            "x_offset": 0.2, # Adjusted x_offset to move slightly right
            "y_offset": 0.4, # Adjusted y_offset to move slightly down
            "fontsize": 8.0
        },
        "KATRINA (2005)": {
            "x_offset": 0.6, # Adjusted x_offset slightly more right
            "y_offset": -0.5, # Adjusted y_offset slightly more down
            "fontsize": 8.0
        },
        "DORIAN (2019)": {
            "x_offset": 0.9, # Adjusted x_offset further right
            "y_offset": 0.7,  # Adjusted y_offset further up
            "fontsize": 8.0
        },
        "BETSY (1965)": {
            "x_offset": 0.9,  # Move Betsy further right
            "y_offset": 0.3,   # Move Betsy slightly up
            "fontsize": 8.0
        },
        "HUGO (1989)": {
            "x_offset": 0.9,   # Move Hugo further right
            "y_offset": -0.5,  # Move Hugo slightly down
            "fontsize": 8.0
        },
        "IRMA (2017)": {
            "x_offset": -0.4, # Move IRMA further left
            "y_offset": -0.5, # Move IRMA slightly down
            "fontsize": 8.0
        },
        "IAN (2022)": {
            "x_offset": 0.4,  # Move IAN slightly right
            "y_offset": -0.1,  # Move IAN slightly down
            "fontsize": 8.0
        },
        "CAMILLE (1969)": {
            "x_offset": -0.6, # Move CAMILLE further left
            "y_offset": 0.4,  # Move CAMILLE slightly up
            "fontsize": 8.0
        },
        "KING (1950)": {
            "x_offset": 0.8,
            "y_offset": -0.8,
            "fontsize": 8.0
        }
    }


def get_direct_placements() -> Dict[str, Dict[str, Any]]:
    """
    Return direct absolute position placements for labels.
    This allows the LLM to position labels at exact coordinates.

    Returns:
        dict: Dictionary with hurricane identifiers as keys and
              placement parameters as values
    """
    # For labels that should bypass both clustering and adjustText
    return {}


def get_iteration_label(iteration: int) -> Dict[str, Any]:
    """
    Return parameters for the iteration label.

    Args:
        iteration: Current iteration number

    Returns:
        dict: Parameters for the iteration label
    """
    return {
        "text": f"Iteration: {iteration}",
        "position": (0.95, 0.05),  # Bottom right position in axes coordinates
        "ha": "right",
        "va": "bottom",
        "fontsize": 10,
        "transform": "axes",  # Use axes coordinates
        "bbox": {
            "facecolor": "white",
            "alpha": 0.7,
            "boxstyle": "round",
            "pad": 0.5
        }
    }