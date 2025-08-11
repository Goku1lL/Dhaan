#!/usr/bin/env python3
"""
Railway deployment entry point for Dhaan Trading System
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for production
os.environ.setdefault('DHAN_CLIENT_ID', '1107931059')
os.environ.setdefault('DHAN_ACCESS_TOKEN', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzU2ODMzMDc4LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwNzkzMTA1OSJ9.nmlNncCNvmF3hg43EF38SqP1gVAWdNkinSewYWQAlF4lpPo6i02tqMr_irAFA0z52a6u346w')

# Import and run the Flask app
if __name__ == '__main__':
    from backend.app import app
    
    # Get port from environment (Railway sets this automatically)
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    
    print(f"🚀 Starting Dhaan Trading System on {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=False  # Set to False for production
    ) 