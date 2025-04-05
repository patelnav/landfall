#!/usr/bin/env python3
"""
List Available Gemini Models

This script lists all available Gemini models that can be accessed with the current API key.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

def list_available_models():
    """
    List all available Gemini models.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        print("Please add your API key to the .env file:")
        print("GEMINI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Get available models
        models = genai.list_models()
        
        # Print available models
        print("\nAvailable Gemini Models:")
        print("-" * 60)
        
        for model in models:
            print(f"Model Name: {model.name}")
            print(f"Display Name: {model.display_name}")
            print(f"Description: {model.description}")
            print(f"Supported Generation Methods: {model.supported_generation_methods}")
            print(f"Input Token Limit: {model.input_token_limit}")
            print(f"Output Token Limit: {model.output_token_limit}")
            
            # Safely check for temperature_range which may not exist on all models
            if hasattr(model, 'temperature_range'):
                print(f"Temperature Range: {model.temperature_range}")
                
            print("-" * 60)
        
    except Exception as e:
        print(f"Error listing models: {str(e)}")

if __name__ == '__main__':
    list_available_models() 