#!/usr/bin/env python3
"""
Script to generate an admin API key for testing purposes.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.v1.auth import generate_api_key

def main():
    """
    Generate an admin API key and display it.
    """
    try:
        # Generate admin API key
        admin_key = generate_api_key('admin')
        
        print("\n" + "="*50)
        print("ADMIN API KEY GENERATED SUCCESSFULLY")
        print("="*50)
        print(f"API Key: {admin_key}")
        print("\nUsage:")
        print(f"Authorization: API-Key {admin_key}")
        print("\nThis key can be used for admin operations like creating products.")
        print("="*50 + "\n")
        
        return admin_key
        
    except Exception as e:
        print(f"Error generating admin API key: {e}")
        return None

if __name__ == "__main__":
    main()