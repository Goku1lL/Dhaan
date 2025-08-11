#!/usr/bin/env python3
"""
Test script to test DhanService methods directly.
"""

from dhan_service import DhanService

def test_service():
    """Test DhanService methods directly."""
    
    print("Testing DhanService...")
    print("=" * 50)
    
    try:
        # Initialize service
        service = DhanService()
        print("Service initialized successfully")
        print(f"Headers: {service.headers}")
        
        # Test portfolio summary
        print("\nTesting get_portfolio_summary...")
        portfolio = service.get_portfolio_summary()
        print(f"Portfolio result: {portfolio}")
        
        # Test positions
        print("\nTesting get_positions...")
        positions = service.get_positions()
        print(f"Positions result: {positions}")
        
        # Test orders
        print("\nTesting get_orders...")
        orders = service.get_orders()
        print(f"Orders result: {orders}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service() 