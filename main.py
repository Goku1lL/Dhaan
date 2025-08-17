#!/usr/bin/env python3
"""
Railway deployment entry point for Dhaan Trading System
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env (override any defaults)
try:
	from dotenv import load_dotenv
	load_dotenv(override=True)
except Exception:
	pass

# Import and run the Flask app
if __name__ == '__main__':
	try:
		from backend.app import app
		
		# Get port from environment (Railway sets this automatically)
		port = int(os.environ.get('PORT', 8000))
		host = '0.0.0.0'
		
		print(f"🚀 Starting Dhaan Trading System on {host}:{port}")
		print(f"📊 Environment: {os.environ.get('FLASK_ENV', 'development')}")
		
		# Enable CORS for production and local development
		from flask_cors import CORS
		CORS(app, origins=[
			"https://dhaan-nu.vercel.app",
			"http://localhost:3000",
			"http://localhost:3030",
			"http://127.0.0.1:3030"
		])
		
		app.run(
			host=host,
			port=port,
			debug=False,  # Set to False for production
			threaded=True  # Enable threading for better performance
		)
	except Exception as e:
		print(f"❌ Failed to start application: {e}")
		import traceback
		traceback.print_exc() 