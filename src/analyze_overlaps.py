#!/usr/bin/env python3
"""
Label Overlap Analysis

This script uses the Gemini API to analyze label overlaps in the South Florida map.
"""

import os
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

def analyze_overlaps(image_path: str) -> str:
    """
    Analyze label overlaps in the provided image using the Gemini API.
    
    Args:
        image_path: Path to the image file
        
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
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Create a model instance
    model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
    
    # Load the image
    image = Image.open(image_path)
    
    # Craft the prompt
    prompt = """
    Analyze the provided image snippet, which shows hurricane landfall labels on a map section of South Florida.
    
    Your task is to identify specific instances where text labels are overlapping each other, making them difficult to read.
    
    List the pairs or groups of labels you see overlapping. For example, "The label 'Hurricane X (YYYY)' overlaps with 'Hurricane Z (YYYY)'."
    
    Focus only on identifying and describing the overlaps. Do not suggest solutions or generate any code.
    """
    
    # Generate content
    response = model.generate_content([prompt, image])
    
    # Return the response text
    return response.text

def main():
    """Main function to analyze label overlaps."""
    # Define paths
    image_path = Path('output') / 'south_florida_landfalls.png'
    
    # Check if image exists
    if not image_path.exists():
        print(f"Error: Image file not found at {image_path}")
        print("Please run south_florida_map.py first to generate the image.")
        return
    
    # Analyze overlaps
    print("Analyzing label overlaps...")
    response = analyze_overlaps(str(image_path))
    
    # Print the response
    print("\nGemini API Response:")
    print(response)
    
    # Save the response to a file
    output_path = Path('output') / 'overlap_analysis.txt'
    with open(output_path, 'w') as f:
        f.write(response)
    
    print(f"\nSaved analysis to {output_path}")

if __name__ == '__main__':
    main() 