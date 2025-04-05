#!/usr/bin/env python3
"""
Agent Loop for Phase 2

This script orchestrates the process of iteratively improving the label layout
using the Gemini 2.0 Flash Thinking model.
"""

import os
import subprocess
import time
import json
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Constants
NUM_ITERATIONS = 6
MODEL_NAME = "gemini-2.0-flash-thinking-exp-01-21"
TIMEOUT = 60  # seconds
PHASE2_OUTPUT_DIR = Path('output') / 'phase2'

def load_api_key() -> str:
    """
    Load the Gemini API key from the .env file.
    
    Returns:
        str: The API key
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
    
    return api_key

def extract_code_from_response(response_text: str) -> str:
    """
    Extract Python code from the LLM response and fix common syntax errors.
    
    Args:
        response_text: The raw response text from the LLM
        
    Returns:
        str: The extracted and fixed Python code
    """
    # Look for code blocks in markdown format
    if "```python" in response_text:
        start = response_text.find("```python") + len("```python")
        end = response_text.find("```", start)
        if end > start:
            code = response_text[start:end].strip()
            
            # Fix common syntax errors
            code = code.replace("if __name__ '__main__':", "if __name__ == '__main__':")
            
            return code
    
    # If no markdown code block, try to extract any code-like content
    lines = response_text.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        if line.strip().startswith('def ') or line.strip().startswith('import ') or line.strip().startswith('from '):
            in_code = True
            code_lines.append(line)
        elif in_code and line.strip() and not line.strip().startswith('#'):
            code_lines.append(line)
        elif in_code and not line.strip():
            code_lines.append(line)
    
    if code_lines:
        code = '\n'.join(code_lines)
        
        # Fix common syntax errors
        code = code.replace("if __name__ '__main__':", "if __name__ == '__main__':")
        
        return code
    
    # If all else fails, return the entire response
    return response_text

def fix_data_path_in_code(code: str, iteration: int) -> str:
    """
    Fix the data path in the code to point to the correct location.
    
    Args:
        code: The code to fix
        iteration: The current iteration number
        
    Returns:
        str: The fixed code
    """
    # The data path should remain in the data directory
    fixed_code = code
    
    # Replace the output path to use the correct iteration number
    fixed_code = fixed_code.replace(
        "output_path = PHASE2_OUTPUT_DIR / 'output_iteration_0.png'",
        f"output_path = PHASE2_OUTPUT_DIR / 'output_iteration_{iteration}.png'"
    )
    
    return fixed_code

def run_plotting_script(script_path: str) -> bool:
    """
    Run the plotting script to generate an image.
    
    Args:
        script_path: Path to the plotting script
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running plotting script: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error running plotting script: {str(e)}")
        return False

def main():
    """Main function to run the agent loop."""
    # Create Phase 2 output directory if it doesn't exist
    PHASE2_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        return
    
    # Configure the API
    genai.configure(api_key=api_key)
    
    # Create a model instance
    print(f"Using model: {MODEL_NAME}")
    model = genai.GenerativeModel(MODEL_NAME)
    
    # Initialize state variables
    current_code = None
    previous_code = None
    previous_image_path = None
    previous_llm_modification = None
    
    # Load the initial plotting code
    initial_script_path = Path('src') / 'plotting_script_v0.py'
    if not initial_script_path.exists():
        print(f"Error: Initial plotting script not found at {initial_script_path}")
        return
    
    with open(initial_script_path, 'r') as f:
        current_code = f.read()
    
    # Create a log file
    log_path = PHASE2_OUTPUT_DIR / 'agent_loop_log.json'
    log_data = []
    
    # Run the loop
    for i in range(NUM_ITERATIONS):
        print(f"\n--- Iteration {i+1}/{NUM_ITERATIONS} ---")
        
        # Fix the data path in the code
        fixed_code = fix_data_path_in_code(current_code, i)
        
        # Save current code to a temporary file
        temp_script_path = Path('src') / 'temp_plotter.py'
        with open(temp_script_path, 'w') as f:
            f.write(fixed_code)
        
        # Run the plotting script
        print("Running plotting script...")
        if not run_plotting_script(str(temp_script_path)):
            print("Failed to run plotting script. Stopping.")
            break
        
        # Get the current image path
        current_image_path = PHASE2_OUTPUT_DIR / f'output_iteration_{i}.png'
        if not current_image_path.exists():
            print(f"Error: Output image not found at {current_image_path}")
            break
        
        # Load the current image
        current_image = Image.open(current_image_path)
        
        # Prepare the prompt
        prompt = f"""
        You are an AI agent improving a Python script that generates a map visualization using Matplotlib and Cartopy. Your goal is to fix overlapping labels.

        **Context:**
        *   **Current Plotting Script:**
            ```python
            {current_code}
            ```
        """
        
        # Add previous image and modification if available
        if previous_image_path and previous_image_path.exists():
            previous_image = Image.open(previous_image_path)
            prompt += f"""
            *   **Image from Previous Script:**
                [Previous image data loaded here]
            *   **Modification made by LLM in Previous Step:**
                ```
                {previous_llm_modification}
                ```
            """
        
        prompt += f"""
        *   **Image Generated by Current Script:**
            [Current image data loaded here]

        **Task:**
        1.  Analyze the current image to identify ONE instance of overlapping text labels. Compare with the previous image (if available) to understand the effect of the last modification.
        2.  Modify the current code to fix the overlap you identified. You might need to adjust the x, y coordinates in `ax.text()` calls or potentially adjust other plotting parameters.
        3.  Output the *entire, complete, modified Python script*. Do not add explanations, comments outside the code, or any text other than the Python code itself, enclosed in markdown triple backticks (```python ... ```).

        **Constraints:** 
        - Ensure the output is runnable Python code that uses Matplotlib/Cartopy.
        - Modify only the plotting logic to improve label layout.
        - DO NOT import or use any external libraries that aren't already imported in the original script (like adjustText).
        - Use only standard Matplotlib functionality to adjust label positions.
        """
        
        # Call the LLM API
        print(f"Sending request to {MODEL_NAME} API...")
        start_time = time.time()
        
        try:
            response = model.generate_content([prompt, current_image])
            
            if time.time() - start_time > TIMEOUT:
                print("Error: API request timed out")
                break
            
            print(f"Received response in {time.time() - start_time:.1f} seconds")
            
            # Extract the code from the response
            new_code = extract_code_from_response(response.text)
            
            # Log the iteration
            log_entry = {
                "iteration": i,
                "prompt": prompt,
                "response": response.text,
                "image_path": str(current_image_path)
            }
            log_data.append(log_entry)
            
            # Save the log
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            # Update state for next iteration
            previous_code = current_code
            current_code = new_code
            previous_image_path = current_image_path
            previous_llm_modification = response.text
            
            print(f"Iteration {i+1} completed. Log saved to {log_path}")
            
        except Exception as e:
            print(f"Error during API call: {str(e)}")
            break
    
    # Clean up temporary files
    if temp_script_path.exists():
        temp_script_path.unlink()
    
    print("\nAgent loop completed.")

if __name__ == '__main__':
    main() 