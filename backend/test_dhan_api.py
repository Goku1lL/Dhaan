#!/usr/bin/env python3
"""
Test script to debug Dhan API calls and identify the specific issues.
"""

import requests
import json
from datetime import datetime

def test_dhan_api():
    """Test Dhan API endpoints to identify issues."""
    
    # Dhan API credentials
    client_id = "1107931059"
    access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzU2ODMzMDc4LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwNzkzMTA1OSJ9.nmlNncCNvmF3hg43EF38SXmm99oKz8GF9dqpP1gVAWdNkinSewYWQAlF4lpPo6i02tqMr_irAFA0z52a6u346w"
    
    # Dhan API base URL
    base_url = "https://api.dhan.co"
    
    # Test different header configurations
    headers_configs = [
        {
            "Content-Type": "application/json",
            "access-token": access_token,
            "X-Client-ID": client_id
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "X-Client-ID": client_id
        },
        {
            "Content-Type": "application/json",
            "access-token": access_token,
            "client-id": client_id
        }
    ]
    
    # Test endpoints
    endpoints = [
        "/fundlimit",
        "/positions", 
        "/orders",
        "/holdings"
    ]
    
    print("Testing Dhan API endpoints...")
    print("=" * 50)
    
    for i, headers in enumerate(headers_configs):
        print(f"\nHeader Configuration {i+1}:")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                print(f"\nTesting: {endpoint}")
                
                response = requests.get(url, headers=headers, timeout=10)
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"Response Data: {json.dumps(data, indent=2)}")
                    except:
                        print(f"Response Text: {response.text[:500]}")
                else:
                    print(f"Error Response: {response.text}")
                    
            except Exception as e:
                print(f"Exception: {e}")
            
            print("-" * 30)

if __name__ == "__main__":
    test_dhan_api() 