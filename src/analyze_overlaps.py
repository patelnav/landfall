#!/usr/bin/env python3
"""
Label Overlap Analysis

This script uses the Gemini API to analyze label overlaps in the South Florida map.
"""

import os
import google.generativeai as genai
import pandas as pd
import argparse
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import time

def get_hurricane_labels(data_path: str) -> list:
    """
    Extract hurricane labels from the dataset.
    
    Args:
        data_path: Path to the CSV file containing landfall data
        
    Returns:
        list: List of hurricane labels in the format "NAME (YEAR)"
    """
    # Read the dataset
    df = pd.read_csv(data_path)
    
    # Define Florida region filter
    filter_min_lon, filter_max_lon = -83.0, -75.0
    filter_min_lat, filter_max_lat = 24.0, 31.0
    
    # Filter data for Florida
    florida_df = df[
        (df['longitude'] >= filter_min_lon) & 
        (df['longitude'] <= filter_max_lon) & 
        (df['latitude'] >= filter_min_lat) & 
        (df['latitude'] <= filter_max_lat)
    ]
    
    # Create list of labels in the format "NAME (YEAR)"
    labels = [f"{row['name']} ({row['year']})" for _, row in florida_df.iterrows()]
    
    return labels

def analyze_overlaps(image_path: str, data_path: str, model_name: str = "gemini-pro-vision", timeout: int = 60) -> str:
    """
    Analyze label overlaps in the provided image using the specified Gemini model.
    
    Args:
        image_path: Path to the image file
        data_path: Path to the CSV file containing landfall data
        model_name: Name of the Gemini model to use
        timeout: Maximum time to wait for response in seconds
        
    Returns:
        str: The API response text
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        print("Please add your API key to the .env file:")
        print("GEMINI_API_KEY='your-api-key-here'")
        return ""
    
    try:
        # Get hurricane labels
        hurricane_labels = get_hurricane_labels(data_path)
        print(f"Found {len(hurricane_labels)} hurricane labels in the Florida region")
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Create a model instance with the specified model
        print(f"Using model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        # Load and resize the image (reduce size to help with API limits)
        image = Image.open(image_path)
        max_size = (1500, 1500)  # Maximum dimension of 1500 pixels
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Craft the prompt
        prompt = f"""
        Analyze this map showing hurricane landfall labels for the Florida region. 
        Focus on the dense clusters where multiple hurricane labels overlap with each other.
        
        Your task is to carefully identify specific instances where text labels are overlapping each other,
        making them difficult to read. Pay attention to the hurricane names and years.
        
        The map contains the following hurricane labels:
        {', '.join(hurricane_labels[:20])}
        ... and {len(hurricane_labels) - 20} more.
        
        First, look at all the regions with dense clusters of labels.
        Then, identify the 5 most severe cases of overlapping labels.
        
        For each overlap case, specify exactly which hurricane labels are involved, including their names and years.
        For example: "The label 'Hurricane Andrew (1992)' severely overlaps with 'Hurricane Katrina (2005)'."
        
        Focus only on identifying and describing the overlaps. Do not suggest solutions or generate any code.
        """
        
        print(f"Sending request to {model_name} API...")
        start_time = time.time()
        
        # Generate content with timeout
        response = model.generate_content([prompt, image])
        
        if time.time() - start_time > timeout:
            return "Error: API request timed out"
        
        print(f"Received response in {time.time() - start_time:.1f} seconds")
        return response.text
        
    except Exception as e:
        print(f"Error during API call: {str(e)}")
        return f"Error: {str(e)}"

def main():
    """Main function to analyze label overlaps."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Analyze hurricane landfall label overlaps using Gemini.')
    parser.add_argument('--model', type=str, default='gemini-2.0-flash-thinking-exp-01-21',
                        help='Gemini model to use (default: gemini-2.0-flash-thinking-exp-01-21)')
    parser.add_argument('--timeout', type=int, default=60,
                        help='API timeout in seconds (default: 60)')
    args = parser.parse_args()
    
    # Define paths
    data_path = Path('data') / 'us_hurricane_landfalls_cat1_5.csv'
    image_path = Path('output') / 'south_florida_landfalls.png'
    
    # Check if files exist
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return
    
    if not image_path.exists():
        print(f"Error: Image file not found at {image_path}")
        print("Please run south_florida_map.py first to generate the image.")
        return
    
    # Analyze overlaps
    print(f"Analyzing label overlaps using {args.model}...")
    response = analyze_overlaps(str(image_path), str(data_path), args.model, args.timeout)
    
    if response.startswith("Error:"):
        print("\nAnalysis failed:")
        print(response)
        return
    
    # Print the response
    print("\nGemini API Response:")
    print("-" * 40)
    print(response)
    print("-" * 40)
    
    # Generate output file name based on model
    model_short_name = args.model.split('-')[-1] if '-' in args.model else args.model
    output_path = Path('output') / f'overlap_analysis_{model_short_name}.txt'
    with open(output_path, 'w') as f:
        f.write(response)
    
    print(f"\nSaved analysis to {output_path}")

if __name__ == '__main__':
    main() 