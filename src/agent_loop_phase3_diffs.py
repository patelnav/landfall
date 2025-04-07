#!/usr/bin/env python3
"""
Agent Loop for Phase 3 - Hurricane Landfall Map Label Optimization with Diff Handling

This script orchestrates the process of iteratively improving the label layout
for Florida hurricane landfalls using the Gemini 2.0 Flash Thinking model.
It adds one cluster of hurricanes at a time, allowing focused optimization.
This version uses code diffs instead of full file replacements.
"""

import os
import subprocess
import time
import json
import base64
import argparse
import shutil
import difflib
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io
import numpy as np
import logging
import re
import patch  # For applying diffs

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

def extract_diff_from_response(response_text: str) -> str:
    """
    Extract diff content from the LLM response.
    
    Args:
        response_text: The raw response text from the LLM
        
    Returns:
        str: The extracted diff text or empty string if not found
    """
    diff_text = ""
    
    # Look for diff blocks in markdown format
    if "```diff" in response_text:
        start = response_text.find("```diff") + len("```diff")
        end = response_text.find("```", start)
        if end > start:
            diff_text = response_text[start:end].strip()
    
    # If no diff block was found, try alternative format
    if not diff_text and "```" in response_text:
        start = response_text.find("```") + len("```")
        end = response_text.find("```", start)
        if end > start:
            # This might be a diff without explicit language marker
            potential_diff = response_text[start:end].strip()
            if potential_diff.startswith("---") or potential_diff.startswith("+++"):
                diff_text = potential_diff
    
    return diff_text

def apply_diff(current_code: str, diff_text: str, logger) -> str:
    """
    Apply a diff to the current code.
    
    Args:
        current_code: The current code content
        diff_text: The diff text to apply
        logger: Logger instance for logging
        
    Returns:
        str: The new code after applying the diff, or the original code if application fails
    """
    if not diff_text:
        logger.warning("No diff text provided.")
        return current_code
    
    try:
        # Ensure diff_text is bytes if the library requires it
        patch_set = patch.fromstring(diff_text.encode('utf-8'))
        
        # Apply patch to current code
        patched_bytes = patch_set.apply(current_code.encode('utf-8'))
        
        if patched_bytes:
            logger.info("Successfully applied diff.")
            return patched_bytes.decode('utf-8')  # Return the new code
        else:
            logger.warning("Failed to apply diff (patch library returned False).")
            return current_code  # Keep the original code
    except Exception as e:
        logger.error(f"Error applying diff: {e}")
        return current_code  # Keep the original code in case of errors

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

def create_prompt(image_path, current_image_path, code_path, iteration, previous_diff=None, previous_image_path=None):
    """Create the prompt for the model."""
    with open(code_path, 'r') as f:
        current_code = f.read()
    
    # Read the previous image if available
    previous_image = None
    if previous_image_path and os.path.exists(previous_image_path):
        with open(previous_image_path, 'rb') as f:
            previous_image = f.read()
    
    prompt = f"""You are an AI agent improving a Python script (`current_code`) that generates a map of Florida hurricane landfalls using Matplotlib/Cartopy and the `adjustText` library. The script plots points incrementally; this is iteration N={iteration}. `adjustText` handles the main layout, but sometimes fails.

**Context:**
*   **Current Iteration Number:** N = {iteration}
*   **Current Plotting Script (`current_code`):**
```python
{current_code}
```

{f'''*   **Image from Previous Script (`previous_image`):** [Image data attached]
*   **Diff applied in Previous Step (`previous_diff`):**
```diff
{previous_diff if previous_diff else "# No previous diff available"}
```
''' if iteration > 0 else ''}

*   **Image Generated by Current Script (`current_image`):** [Image data attached]

**Task:**
1.  Analyze the `current_image`, focusing on the layout generated primarily by `adjustText`. Identify the ONE WORST remaining overlap or label placement issue, especially concerning the newly added cluster or interactions between clusters.
2.  Generate a code diff in standard `diff -u` format to modify the `current_code`.
3.  The **primary goal** of the diff should be to add a *new* specific `ax.text(x, y, "Label (YEAR)", ...)` call *after* the main `adjust_text(...)` call. This new call manually sets the precise coordinates (x, y) for the single problematic label you identified, effectively overriding the position `adjustText` chose for it. Choose coordinates that resolve the issue identified in step 1.
4.  Do NOT modify the main `adjust_text(...)` call or its parameters in this diff unless absolutely necessary and you explain why in a comment within the diff context. Do not modify data loading or loop logic.
5.  Output **only the diff block**, correctly formatted and enclosed in markdown triple backticks (```diff ... ```).

**Self-Correction Hint:** Review the `previous_image` and `previous_diff`. If the last change didn't improve the specific issue it targeted, try fixing a *different* problematic label in this iteration.
"""
    
    return prompt, current_code

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
    
    # Create logger
    logger = logging.getLogger()
    
    # Set up the model
    model = setup_model()
    if not model:
        logger.error("Failed to set up the model. Exiting.")
        return
    
    # Initialize variables for tracking
    previous_diff = None
    total_cost = 0.0
    
    # Loop through iterations
    for i in range(starting_iteration, starting_iteration + num_iterations):
        print(f"\nStarting iteration {i}...")
        logger.info(f"Starting iteration {i}")
        
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
            logger.info(f"Running plotting script for iteration {i}")
            
            # Copy the template file to the code directory for iteration 0
            if i == starting_iteration:
                shutil.copy("src/plotting_script_phase3_adjustText_focused.py", current_iteration_code_path)
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
        logger.info(f"Generating hurricane map for iteration {i}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running plotting script: {result.stderr}")
            print(f"Error running plotting script: {result.stderr}")
            return
        
        # Skip model call for final iteration (we just want to generate the final image)
        if i == starting_iteration + num_iterations - 1:
            print(f"Completed final iteration {i}")
            logger.info(f"Completed final iteration {i}")
            break
        
        # Create the prompt for the model
        print("Preparing input for model...")
        logger.info("Preparing input for model")
        
        # Create the prompt
        prompt, current_code = create_prompt(
            current_image_path, 
            current_image_path, 
            current_iteration_code_path, 
            i,
            previous_diff,
            previous_image_path
        )
        
        # Store the current code for comparison after diff application
        previous_code = current_code
        
        # Estimate the cost of this model call
        cost_estimate = estimate_cost(prompt)
        total_cost += cost_estimate
        
        # Call the model
        print("Calling Gemini model...")
        logger.info("Calling Gemini model")
        start_time = time.time()
        
        # Convert the image to bytes
        current_image_bytes = convert_image_to_bytes(current_image_path)
        
        # Convert previous image to bytes if it exists
        previous_image_bytes = None
        if previous_image_path and os.path.exists(previous_image_path):
            previous_image_bytes = convert_image_to_bytes(previous_image_path)
        
        # Prepare model contents
        contents = [prompt, current_image_bytes]
        if previous_image_bytes:
            contents.append(previous_image_bytes)
        
        # Call the model with the multimodal prompt
        response = model.generate_content(
            contents=contents,
            generation_config={"temperature": 0.2},
            safety_settings=SAFETY_SETTINGS
        )
        
        # Extract the diff from the response
        diff_text = extract_diff_from_response(response.text)
        if not diff_text:
            logger.error("No diff found in the model response")
            print("No diff found in the model response.")
            # Create a next iteration file anyway, with unchanged code
            next_iteration_code_path = CODE_DIR / f"plotting_script_phase3_iter_{i+1}.py"
            with open(next_iteration_code_path, 'w') as f:
                f.write(current_code)
            continue
        
        # Apply the diff to the current code
        new_code = apply_diff(current_code, diff_text, logger)
        
        # Save the new code to the next iteration
        next_iteration_code_path = CODE_DIR / f"plotting_script_phase3_iter_{i+1}.py"
        with open(next_iteration_code_path, 'w') as f:
            f.write(new_code)
        
        # Save the model's response to a log file
        response_log_path = LOG_DIR / f"response_iter_{i}.txt"
        with open(response_log_path, 'w') as f:
            f.write(response.text)
        
        # Save the diff to a log file
        diff_log_path = LOG_DIR / f"diff_iter_{i}.diff"
        with open(diff_log_path, 'w') as f:
            f.write(diff_text)
        
        # Keep track of the modification for the next iteration's context
        previous_diff = diff_text
        
        # Log the completion of this iteration
        elapsed_time = time.time() - start_time
        print(f"Completed iteration {i} in {elapsed_time:.1f} seconds")
        logger.info(f"Completed iteration {i} in {elapsed_time:.1f} seconds")
    
    # Print the final cost estimate
    print(f"\nAgent loop completed. Total cost: {total_cost:.4f} USD")
    logger.info(f"Agent loop completed. Total cost: {total_cost:.4f} USD")
    print(f"Log file saved to: {log_file}")

def main():
    """Main function to run the agent loop."""
    parser = argparse.ArgumentParser(description='Run the hurricane landfall map agent loop with diff handling.')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations to run')
    parser.add_argument('--start', type=int, default=0, help='Iteration number to start from')
    args = parser.parse_args()
    
    run_agent_loop(args.iterations, args.start)

if __name__ == '__main__':
    main() 