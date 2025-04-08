#!/usr/bin/env python3
"""
Run the algorithmic approach for hurricane label placement.

This script runs the plotting_script_phase3_algo.py script for multiple iterations
to generate a series of maps showing the progression of the algorithmic approach.
"""

import subprocess
import time
import argparse
from pathlib import Path
import os
import shutil
import logging
from datetime import datetime

# Output directories
OUTPUT_DIR = Path('output') / 'phase3_algo'
IMAGE_DIR = OUTPUT_DIR / 'images'
LOG_DIR = OUTPUT_DIR / 'logs'

# Ensure directories exist
for dir_path in [OUTPUT_DIR, IMAGE_DIR, LOG_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

def run_iterations(num_iterations: int, start_iteration: int = 0) -> None:
    """
    Run the algorithmic approach for the specified number of iterations.
    
    Args:
        num_iterations: Number of iterations to run
        start_iteration: Iteration number to start from
    """
    # Set up logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"algorithmic_approach_{timestamp}.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Loop through iterations
    for i in range(start_iteration, start_iteration + num_iterations):
        print(f"\nStarting iteration {i}...")
        logging.info(f"Starting iteration {i}")
        
        # Run the plotting script
        start_time = time.time()
        result = subprocess.run(
            ["python", "src/plotting_script_phase3_algo.py", str(i)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logging.error(f"Error running plotting script: {result.stderr}")
            print(f"Error running plotting script: {result.stderr}")
            return
        
        # Log the completion of this iteration
        elapsed_time = time.time() - start_time
        print(f"Completed iteration {i} in {elapsed_time:.1f} seconds")
        logging.info(f"Completed iteration {i} in {elapsed_time:.1f} seconds")
    
    print(f"\nAlgorithmic approach completed. Log file saved to: {log_file}")
    logging.info("Algorithmic approach completed")

def create_animation() -> None:
    """Create an animation from the generated images."""
    # Check if ImageMagick is installed
    try:
        subprocess.run(["magick", "--version"], capture_output=True, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: ImageMagick is not installed or not in PATH.")
        print("Please install ImageMagick to create the animation.")
        return
    
    # Create the animation
    print("Creating animation...")
    subprocess.run(
        [
            "magick",
            "convert",
            "-delay", "100",
            "-loop", "0",
            str(IMAGE_DIR / "florida_algo_iter_*.png"),
            str(OUTPUT_DIR / "florida_algo_animation.gif")
        ],
        check=True
    )
    
    print(f"Animation saved to {OUTPUT_DIR / 'florida_algo_animation.gif'}")

def main():
    """Main function to run the algorithmic approach."""
    parser = argparse.ArgumentParser(description='Run the algorithmic approach for hurricane label placement.')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations to run')
    parser.add_argument('--start', type=int, default=0, help='Iteration number to start from')
    parser.add_argument('--create-animation', action='store_true', help='Create an animation from the generated images')
    args = parser.parse_args()
    
    # Run the iterations
    run_iterations(args.iterations, args.start)
    
    # Create animation if requested
    if args.create_animation:
        create_animation()

if __name__ == "__main__":
    main() 