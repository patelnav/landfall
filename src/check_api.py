#!/usr/bin/env python3
"""
Gemini API Connectivity Check

This script tests the connection to the Gemini API using a simple prompt.
"""

import os
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

def check_api_connection(api_key: str) -> bool:
    """
    Test the connection to the Gemini API.
    
    Args:
        api_key: The API key for Gemini
        
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Create a model instance
        model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
        
        # Test with a simple prompt
        response = model.generate_content("Hello! This is a test message.")
        
        # Check if we got a response
        if response and response.text:
            print("API Connection Successful!")
            print(f"Response: {response.text}")
            return True
        else:
            print("API Connection Failed: No response received")
            return False
            
    except Exception as e:
        print(f"API Connection Failed: {str(e)}")
        return False

def main():
    """Main function to check API connectivity."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key from environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file")
        print("Please add your API key to the .env file:")
        print("GEMINI_API_KEY='your-api-key-here'")
        return
    
    # Check API connection
    check_api_connection(api_key)

if __name__ == '__main__':
    main() 