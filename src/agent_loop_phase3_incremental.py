#!/usr/bin/env python3
"""
Agent Loop for Phase 3 - Hurricane Landfall Map Label Optimization with Incremental Clustering

This script orchestrates the process of iteratively improving the label layout
for Florida hurricane landfalls using the Gemini 2.0 Flash Thinking model.
It adds one cluster of hurricanes at a time, allowing focused optimization.
"""

import os
import subprocess
import time
import json
import base64
import argparse
import shutil
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io
import numpy as np
import logging
import re

# Constants
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
TIMEOUT = 300  # seconds
API_KEY_FILE = Path('api_key.txt')

# Output directories
OUTPUT_DIR = Path('output') / 'phase3'
IMAGE_DIR = OUTPUT_DIR / 'images'
CODE_DIR = OUTPUT_DIR / 'code'
LOG_DIR = OUTPUT_DIR / 'logs'

# Safety settings
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
]

# Ensure directories exist
for dir_path in [OUTPUT_DIR, IMAGE_DIR, CODE_DIR, LOG_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)

def load_api_key():
    """Load the API key from environment variable."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        print("Please add your API key to the .env file:")
        print("GEMINI_API_KEY='your-api-key-here'")
        return None
    
    return api_key

def setup_model():
    """Set up the Gemini model."""
    api_key = load_api_key()
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL_NAME)
        return model
    except Exception as e:
        print(f"Error setting up model: {e}")
        return None

def convert_image_to_bytes(image_path):
    """Convert an image to bytes for the model."""
    try:
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        return {"mime_type": "image/png", "data": image_bytes}
    except Exception as e:
        print(f"Error reading image file: {e}")
        return None

def extract_code_from_response(response_text: str) -> str:
    """
    Extract Python code from the LLM response and fix any backtick issues.
    
    Args:
        response_text: The raw response text from the LLM
        
    Returns:
        str: The extracted Python code
    """
    code = ""
    
    # Look for code blocks in markdown format
    if "```python" in response_text:
        start = response_text.find("```python") + len("```python")
        end = response_text.find("```", start)
        if end > start:
            code = response_text[start:end].strip()
    elif "```" in response_text:
        start = response_text.find("```") + len("```")
        end = response_text.find("```", start)
        if end > start:
            code = response_text[start:end].strip()
    else:
        # If no markdown code block is found, return the whole response
        # This is a fallback, but not ideal
        code = response_text
    
    # Check if the code still has backticks at the beginning
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    elif code.startswith("```"):
        code = code[len("```"):].strip()
    
    # Check if the code still has backticks at the end
    if code.endswith("```"):
        code = code[:-3].strip()
    
    return code

def estimate_cost(prompt: str, image_paths: list = None) -> float:
    """
    Estimate the cost of an API call.
    
    Args:
        prompt: The text prompt
        image_paths: List of paths to images
        
    Returns:
        float: Estimated cost in USD
    """
    # Cost estimation based on token count and images
    # Flash model is estimated at $0.00035 per 1K input tokens
    # and $0.0015 per 1K output tokens
    
    # Estimate text tokens (rough approximation)
    text_tokens = len(prompt) / 4  # Approximate tokens from characters
    
    # Estimate image tokens
    image_tokens = 0
    if image_paths:
        # Assuming each image is roughly 500K tokens 
        # (this is a simplification, actual size varies)
        image_tokens = len(image_paths) * 500000
    
    # Total input tokens
    total_input_tokens = text_tokens + image_tokens
    
    # Estimate output tokens (assuming output is roughly same size as prompt)
    output_tokens = len(prompt) / 4
    
    # Calculate cost in USD
    input_cost = (total_input_tokens / 1000) * 0.00035
    output_cost = (output_tokens / 1000) * 0.0015
    
    total_cost = input_cost + output_cost
    
    return total_cost

def create_prompt(image_path, code_path, iteration):
    """Create the prompt for the model."""
    with open(code_path, 'r') as f:
        current_code = f.read()
    
    with open(image_path, 'rb') as f:
        current_image = f.read()
    
    prompt = f"""You are an AI assistant tasked with optimizing hurricane landfall map label placements.

Task: Improve the legibility of hurricane labels on the map by making targeted adjustments.

Here is the current state:
- The map shows hurricane landfalls along the US East Coast, with a focus on Florida
- We're using an incremental approach, adding one cluster of hurricanes per iteration
- This is iteration {iteration}
- The script currently places labels near their points and uses adjustText for basic layout
- adjustText may leave some overlaps or positioning issues

IMPORTANT: I will provide you with the CURRENT CODE that needs to be modified. DO NOT create a completely new script. 
Only make a small, focused change to the provided code.

Your task:
1. Analyze the current image to identify the WORST remaining label overlap or unreadable label
2. Modify the existing code by adding ONE manual label override AFTER the adjust_text call
3. Provide x, y coordinates for the problematic label to place it better
4. Focus on the most severe issue first - don't try to fix everything at once

Example modification (only add this after the adjust_text call):
```python
# Add a manual override for a specific label
for text in all_texts:
    if text.get_text() == "PROBLEMATIC_LABEL":
        text.set_position((better_x, better_y))
```

Here's the current code:
```python
{current_code}
```

Make sure your changes are minimal and focused on just the most problematic label.
Return the COMPLETE modified script including your single targeted improvement.
"""
    
    return prompt, current_code, current_image

def run_agent_loop(num_iterations: int, starting_iteration: int = 0) -> None:
    """
    Run the agent loop for the specified number of iterations.
    
    Args:
        num_iterations: Number of iterations to run
        starting_iteration: Iteration number to start from
    """
    # Create output directories if they don't exist
    for dir_path in [OUTPUT_DIR, IMAGE_DIR, CODE_DIR, LOG_DIR]:
        dir_path.mkdir(exist_ok=True, parents=True)
    
    # Set up logging
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"agent_loop_{timestamp}.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Set up the model
    model = setup_model()
    if not model:
        logging.error("Failed to set up the model. Exiting.")
        return
    
    # Initialize variables for tracking
    previous_modification = None
    total_cost = 0.0
    
    # Loop through iterations
    for i in range(starting_iteration, starting_iteration + num_iterations):
        print(f"\nStarting iteration {i}...")
        logging.info(f"Starting iteration {i}")
        
        # Define paths for current iteration
        current_iteration_code_path = CODE_DIR / f"plotting_script_phase3_iter_{i}.py"
        current_image_path = IMAGE_DIR / f"florida_iter_{i}.png"
        
        # If this is not the first iteration, set up the previous image path
        previous_image_path = None
        if i > starting_iteration:
            previous_image_path = IMAGE_DIR / f"florida_iter_{i-1}.png"
        
        # For iteration 0 or when code doesn't exist, copy the template
        if i == starting_iteration or not current_iteration_code_path.exists():
            print(f"Running plotting script for iteration {i}...")
            logging.info(f"Running plotting script for iteration {i}")
            
            # Copy the template file to the code directory for iteration 0
            if i == starting_iteration:
                shutil.copy("src/plotting_script_phase3_incremental.py", current_iteration_code_path)
            else:
                # For subsequent iterations, we'll need to make sure we have a script file to run
                prev_iteration_code_path = CODE_DIR / f"plotting_script_phase3_iter_{i-1}.py"
                shutil.copy(prev_iteration_code_path, current_iteration_code_path)
        
        # Always run the plotting script to generate or update the image
        command = [
            "python", 
            str(current_iteration_code_path), 
            str(i)
        ]
        print(f"Generating hurricane map for iteration {i}...")
        logging.info(f"Generating hurricane map for iteration {i}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Error running plotting script: {result.stderr}")
            print(f"Error running plotting script: {result.stderr}")
            return
        
        # Skip model call for final iteration (we just want to generate the final image)
        if i == starting_iteration + num_iterations - 1:
            print(f"Completed final iteration {i}")
            logging.info(f"Completed final iteration {i}")
            break
        
        # Create the prompt for the model
        print("Preparing input for model...")
        logging.info("Preparing input for model")
        
        # Create the prompt
        prompt, current_code, current_image = create_prompt(
            current_image_path, 
            current_iteration_code_path, 
            i
        )
        
        # Estimate the cost of this model call
        cost_estimate = estimate_cost(prompt)
        total_cost += cost_estimate
        
        # Call the model
        print("Calling Gemini model...")
        logging.info("Calling Gemini model")
        start_time = time.time()
        
        # Convert the image to bytes
        image_bytes = convert_image_to_bytes(current_image_path)
        
        # Call the model with the multimodal prompt
        response = model.generate_content(
            contents=[
                prompt,
                image_bytes
            ],
            generation_config={"temperature": 0.2},
            safety_settings=SAFETY_SETTINGS
        )
        
        # Extract the code from the response
        code = extract_code_from_response(response.text)
        if not code:
            logging.error("No code found in the model response")
            print("No code found in the model response. Exiting.")
            return
        
        # Save the modified code to the next iteration
        next_iteration_code_path = CODE_DIR / f"plotting_script_phase3_iter_{i+1}.py"
        with open(next_iteration_code_path, 'w') as f:
            f.write(code)
        
        # Save the model's response to a log file
        response_log_path = LOG_DIR / f"response_iter_{i}.txt"
        with open(response_log_path, 'w') as f:
            f.write(response.text)
        
        # Keep track of the modification for the next iteration's context
        previous_modification = response.text
        
        # Log the completion of this iteration
        elapsed_time = time.time() - start_time
        print(f"Completed iteration {i} in {elapsed_time:.1f} seconds")
        logging.info(f"Completed iteration {i} in {elapsed_time:.1f} seconds")
    
    # Print the final cost estimate
    print(f"\nAgent loop completed. Total cost: {total_cost:.4f} USD")
    logging.info(f"Agent loop completed. Total cost: {total_cost:.4f} USD")
    print(f"Log file saved to: {log_file}")

def main():
    """Main function to run the agent loop."""
    parser = argparse.ArgumentParser(description='Run the hurricane landfall map agent loop with incremental clustering.')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations to run')
    parser.add_argument('--start', type=int, default=0, help='Iteration number to start from')
    args = parser.parse_args()
    
    run_agent_loop(args.iterations, args.start)

if __name__ == '__main__':
    main() 