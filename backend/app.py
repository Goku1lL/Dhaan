from flask import Flask, jsonify, request
from flask_cors import CORS
from .dhan_service import DhanService
from .market_scanner_manager import MarketScannerManager
import os
import logging

# Paper Trading Manager
try:
    from .paper_trading_manager import paper_trading_manager
    PAPER_TRADING_AVAILABLE = True
    print("✅ Paper Trading Manager loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import Paper Trading Manager: {e}")
    PAPER_TRADING_AVAILABLE = False

# Strategy Paper Trading Integration
try:
    from .strategy_paper_trading_integration import initialize_strategy_paper_trading_integration, get_strategy_paper_trading_integration
    STRATEGY_PAPER_TRADING_AVAILABLE = True
    print("✅ Strategy Paper Trading Integration loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import Strategy Paper Trading Integration: {e}")
    STRATEGY_PAPER_TRADING_AVAILABLE = False

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Dhan service
dhan_service = DhanService()

# Initialize Market Scanner Manager
market_scanner_manager = MarketScannerManager(dhan_service)

# Initialize Strategy Paper Trading Integration
if STRATEGY_PAPER_TRADING_AVAILABLE and PAPER_TRADING_AVAILABLE:
    strategy_integration = initialize_strategy_paper_trading_integration(
        market_scanner_manager, paper_trading_manager
    )
    # Start strategy processing loop to auto-process opportunities periodically
    try:
        # Run every 30 seconds by default
        strategy_integration.run_strategy_processing_loop(interval_seconds=30)
        logger.info("Strategy processing background loop started")
    except Exception as _bg_err:
        logger.error(f"Failed to start strategy processing loop: {_bg_err}")
    print("✅ Strategy Paper Trading Integration initialized")
else:
    strategy_integration = None
    print("❌ Strategy Paper Trading Integration not available")

@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint for Railway."""
    from datetime import datetime
    return jsonify({
        'status': 'healthy',
        'service': 'Dhaan Trading System',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get dashboard data including portfolio summary and active positions."""
    try:
        # Get portfolio summary
        portfolio_summary = dhan_service.get_portfolio_summary()
        
        # Get active positions
        positions = dhan_service.get_positions()
        
        # Get recent orders
        orders = dhan_service.get_orders()
        
        return jsonify({
            'portfolio_summary': portfolio_summary,
            'active_positions': positions,
            'recent_orders': orders[:5] if orders else [],  # Last 5 orders
            'system_status': 'online'
        })
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions."""
    try:
        positions = dhan_service.get_positions()
        return jsonify(positions)
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get order history."""
    try:
        orders = dhan_service.get_orders()
        return jsonify(orders)
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Get trading strategies."""
    try:
        strategies = dhan_service.get_strategies()
        return jsonify(strategies)
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-symbols', methods=['GET'])
def get_market_symbols():
    """Get market symbols for trading."""
    try:
        # This would typically return a list of tradeable symbols
        # For now, return a basic list
        symbols = [
            {'symbol': 'RELIANCE', 'name': 'Reliance Industries', 'lastPrice': 2450.50, 'change': 12.30},
            {'symbol': 'TCS', 'name': 'Tata Consultancy Services', 'lastPrice': 3850.00, 'change': -15.75},
            {'symbol': 'INFY', 'name': 'Infosys', 'lastPrice': 1580.00, 'change': 8.25},
            {'symbol': 'HDFC', 'name': 'HDFC Bank', 'lastPrice': 1680.00, 'change': -5.50},
            {'symbol': 'ICICIBANK', 'name': 'ICICI Bank', 'lastPrice': 920.50, 'change': 4.75}
        ]
        return jsonify(symbols)
    except Exception as e:
        logger.error(f"Error getting market symbols: {e}")
        return jsonify({'error': str(e)}), 500

# NEW MARKET SCANNER ENDPOINTS

@app.route('/api/market-scanner/scan-results', methods=['GET'])
def get_market_scan_results():
    """Get latest market scan results."""
    try:
        result = market_scanner_manager.get_scan_results()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting market scan results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-scanner/universes', methods=['GET'])
def get_stock_universes():
    """Get available stock universes for configuration."""
    try:
        # Import the stock universe configurations
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from dhan_advanced_algo.stock_universe_config import (
            CONSERVATIVE_UNIVERSE, AGGRESSIVE_UNIVERSE, BANKING_UNIVERSE,
            IT_UNIVERSE, PHARMA_UNIVERSE, AUTO_UNIVERSE, INTRADAY_UNIVERSE,
            SWING_UNIVERSE, POSITIONAL_UNIVERSE
        )
        
        universes = [
            {
                "id": "default",
                "name": "Default (174 stocks)", 
                "description": "Balanced universe with NIFTY 50, NEXT 50, and sector leaders",
                "stock_count": 174,
                "category": "balanced"
            },
            {
                "id": "conservative",
                "name": "Conservative (50 stocks)",
                "description": "NIFTY 50 stocks - high liquidity, stable companies",
                "stock_count": len(CONSERVATIVE_UNIVERSE),
                "category": "conservative"
            },
            {
                "id": "aggressive", 
                "name": "Aggressive (300+ stocks)",
                "description": "NIFTY 500 universe - maximum market coverage",
                "stock_count": len(AGGRESSIVE_UNIVERSE),
                "category": "aggressive"
            },
            {
                "id": "banking",
                "name": "Banking Sector",
                "description": "Banking and financial services stocks only",
                "stock_count": len(BANKING_UNIVERSE),
                "category": "sector"
            },
            {
                "id": "it",
                "name": "IT Sector", 
                "description": "Information Technology and software companies",
                "stock_count": len(IT_UNIVERSE),
                "category": "sector"
            },
            {
                "id": "pharma",
                "name": "Pharmaceutical Sector",
                "description": "Pharmaceutical and healthcare companies", 
                "stock_count": len(PHARMA_UNIVERSE),
                "category": "sector"
            },
            {
                "id": "auto",
                "name": "Automotive Sector",
                "description": "Automotive and auto ancillary companies",
                "stock_count": len(AUTO_UNIVERSE),
                "category": "sector"
            },
            {
                "id": "intraday",
                "name": "Intraday Trading",
                "description": "High-volume, liquid stocks ideal for day trading",
                "stock_count": len(INTRADAY_UNIVERSE),
                "category": "strategy"
            },
            {
                "id": "swing",
                "name": "Swing Trading",
                "description": "NIFTY 50 stocks suitable for swing trading",
                "stock_count": len(SWING_UNIVERSE),
                "category": "strategy"
            },
            {
                "id": "positional",
                "name": "Positional Trading",
                "description": "Comprehensive universe for long-term positions", 
                "stock_count": len(POSITIONAL_UNIVERSE),
                "category": "strategy"
            }
        ]
        
        return jsonify({"universes": universes})
        
    except Exception as e:
        logger.error(f"Error getting stock universes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-scanner/universe', methods=['POST'])
def update_stock_universe():
    """Update the stock universe for scanning."""
    try:
        data = request.get_json()
        universe_id = data.get('universe_id')
        
        if not universe_id:
            return jsonify({'error': 'universe_id is required'}), 400
        
        # Import universe configurations
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from dhan_advanced_algo.stock_universe_config import (
            CONSERVATIVE_UNIVERSE, AGGRESSIVE_UNIVERSE, BANKING_UNIVERSE,
            IT_UNIVERSE, PHARMA_UNIVERSE, AUTO_UNIVERSE, INTRADAY_UNIVERSE,
            SWING_UNIVERSE, POSITIONAL_UNIVERSE
        )
        
        # Map universe IDs to actual lists
        universe_map = {
            "default": None,  # Use default from scanner
            "conservative": CONSERVATIVE_UNIVERSE,
            "aggressive": AGGRESSIVE_UNIVERSE,
            "banking": BANKING_UNIVERSE,
            "it": IT_UNIVERSE,
            "pharma": PHARMA_UNIVERSE,
            "auto": AUTO_UNIVERSE,
            "intraday": INTRADAY_UNIVERSE,
            "swing": SWING_UNIVERSE,
            "positional": POSITIONAL_UNIVERSE
        }
        
        if universe_id not in universe_map:
            return jsonify({'error': f'Invalid universe_id: {universe_id}'}), 400
        
        # Update the scanner's universe
        result = market_scanner_manager.update_stock_universe(universe_id, universe_map[universe_id])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error updating stock universe: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-scanner/universe', methods=['GET'])
def get_current_universe():
    """Get the currently selected stock universe."""
    try:
        result = market_scanner_manager.get_current_universe()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting current universe: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-scanner/start', methods=['POST'])
def start_market_scanning():
    """Start market scanning."""
    try:
        result = market_scanner_manager.start_scanning()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting market scanning: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-scanner/stop', methods=['POST'])
def stop_market_scanning():
    """Stop market scanning."""
    try:
        result = market_scanner_manager.stop_scanning()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping market scanning: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-scanner/status', methods=['GET'])
def get_scanner_status():
    """Get scanner status."""
    try:
        status = market_scanner_manager.get_scanner_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting scanner status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-scanner/eod-report', methods=['GET'])
def get_eod_report():
    """Get EOD report."""
    try:
        date = request.args.get('date')  # Optional date parameter
        report = market_scanner_manager.generate_eod_report(date)
        return jsonify(report)
    except Exception as e:
        logger.error(f"Error generating EOD report: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies/<strategy_id>/enable', methods=['POST'])
def enable_strategy(strategy_id):
    """Enable a trading strategy."""
    try:
        # This would enable/disable a specific strategy
        # For now, return success
        return jsonify({'status': 'success', 'message': f'Strategy {strategy_id} enabled'})
    except Exception as e:
        logger.error(f"Error enabling strategy: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategies/<strategy_id>/disable', methods=['POST'])
def disable_strategy(strategy_id):
    """Disable a trading strategy."""
    try:
        # This would enable/disable a specific strategy
        # For now, return success
        return jsonify({'status': 'success', 'message': f'Strategy {strategy_id} disabled'})
    except Exception as e:
        logger.error(f"Error disabling strategy: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/performance', methods=['GET'])
def get_performance_analytics():
    """Get performance analytics data."""
    try:
        # Mock performance data for now
        performance_data = {
            "daily_returns": [0.5, -0.2, 1.1, 0.8, -0.3, 1.5, 0.7],
            "weekly_returns": [2.1, -1.5, 3.2, 1.8],
            "monthly_returns": [5.5, -2.3, 8.1],
            "total_return": 12.5,
            "sharpe_ratio": 1.8,
            "max_drawdown": -5.2,
            "win_rate": 68.5
        }
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/market-overview', methods=['GET'])
def get_market_overview():
    """Get market overview data."""
    try:
        # Mock market overview data
        market_data = {
            "market_status": "CLOSED",
            "nifty_50": {"value": 19850.25, "change": 125.30, "change_percent": 0.63},
            "bank_nifty": {"value": 44250.80, "change": -85.20, "change_percent": -0.19},
            "sensex": {"value": 66500.45, "change": 200.15, "change_percent": 0.30},
            "vix": {"value": 13.25, "change": -0.85, "change_percent": -6.02},
            "sector_performance": [
                {"name": "Technology", "change": 1.2},
                {"name": "Banking", "change": -0.3},
                {"name": "Energy", "change": 0.8},
                {"name": "Healthcare", "change": 0.5},
                {"name": "Others", "change": 0.1}
            ]
        }
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return jsonify({'error': str(e)}), 500

# =====================================
# STRATEGY PAPER TRADING API ENDPOINTS
# =====================================

@app.route('/api/strategy-trading/status', methods=['GET'])
def get_strategy_trading_status():
    """Get strategy paper trading status and configuration."""
    try:
        if not STRATEGY_PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Strategy paper trading not available'}), 503
        
        integration = get_strategy_paper_trading_integration()
        if not integration:
            return jsonify({'error': 'Strategy integration not initialized'}), 503
        
        status = integration.get_auto_trading_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting strategy trading status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-trading/auto-trading/enable', methods=['POST'])
def enable_strategy_auto_trading():
    """Enable automatic strategy-based paper trading."""
    try:
        if not STRATEGY_PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Strategy paper trading not available'}), 503
        
        integration = get_strategy_paper_trading_integration()
        if not integration:
            return jsonify({'error': 'Strategy integration not initialized'}), 503
        
        result = integration.enable_auto_trading()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error enabling strategy auto trading: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-trading/auto-trading/disable', methods=['POST'])
def disable_strategy_auto_trading():
    """Disable automatic strategy-based paper trading."""
    try:
        if not STRATEGY_PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Strategy paper trading not available'}), 503
        
        integration = get_strategy_paper_trading_integration()
        if not integration:
            return jsonify({'error': 'Strategy integration not initialized'}), 503
        
        result = integration.disable_auto_trading()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error disabling strategy auto trading: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-trading/process-opportunities', methods=['POST'])
def process_strategy_opportunities():
    """Process market scanner opportunities and execute strategy-based paper trades."""
    try:
        if not STRATEGY_PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Strategy paper trading not available'}), 503
        
        integration = get_strategy_paper_trading_integration()
        if not integration:
            return jsonify({'error': 'Strategy integration not initialized'}), 503
        
        # Run async function
        import asyncio
        result = asyncio.run(integration.process_market_opportunities())
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing strategy opportunities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-trading/performance', methods=['GET'])
def get_strategy_performance():
    """Get comprehensive strategy performance summary."""
    try:
        if not STRATEGY_PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Strategy paper trading not available'}), 503
        
        integration = get_strategy_paper_trading_integration()
        if not integration:
            return jsonify({'error': 'Strategy integration not initialized'}), 503
        
        performance = integration.get_strategy_performance()
        return jsonify(performance)
        
    except Exception as e:
        logger.error(f"Error getting strategy performance: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-trading/active-trades', methods=['GET'])
def get_strategy_active_trades():
    """Get list of currently active strategy trades."""
    try:
        if not STRATEGY_PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Strategy paper trading not available'}), 503
        
        integration = get_strategy_paper_trading_integration()
        if not integration:
            return jsonify({'error': 'Strategy integration not initialized'}), 503
        
        trades = integration.get_active_strategy_trades()
        return jsonify(trades)
        
    except Exception as e:
        logger.error(f"Error getting strategy active trades: {e}")
        return jsonify({'error': str(e)}), 500

# =====================================
# END STRATEGY PAPER TRADING API ENDPOINTS
# =====================================

# =====================================
# PAPER TRADING API ENDPOINTS
# =====================================

@app.route('/api/paper-trading/mode', methods=['GET'])
def get_trading_mode():
    """Get current trading mode (PAPER or LIVE)."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        result = paper_trading_manager.get_trading_mode()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting trading mode: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/mode', methods=['POST'])
def set_trading_mode():
    """Set trading mode (PAPER or LIVE)."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        data = request.get_json()
        if not data or 'mode' not in data:
            return jsonify({'error': 'Mode is required'}), 400
        
        result = paper_trading_manager.set_trading_mode(data['mode'])
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error setting trading mode: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/orders', methods=['POST'])
def place_paper_order():
    """Place a paper trading order."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Order data is required'}), 400
        
        # Validate required fields
        required_fields = ['symbol', 'side', 'quantity', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        result = paper_trading_manager.place_paper_order(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logging.error(f"Error placing paper order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/orders/<order_id>/cancel', methods=['POST'])
def cancel_paper_order(order_id):
    """Cancel a paper trading order."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        result = paper_trading_manager.cancel_paper_order(order_id)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error cancelling paper order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/portfolio', methods=['GET'])
def get_paper_portfolio():
    """Get paper trading portfolio summary."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        result = paper_trading_manager.get_paper_portfolio()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting paper portfolio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/positions', methods=['GET'])
def get_paper_positions():
    """Get paper trading positions."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        result = paper_trading_manager.get_paper_positions()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting paper positions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/positions/<symbol>/close', methods=['POST'])
def close_paper_position(symbol):
    """Close a paper trading position."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        data = request.get_json() or {}
        quantity = data.get('quantity')  # Optional - None means close full position
        
        result = paper_trading_manager.close_paper_position(symbol, quantity)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error closing paper position: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/orders', methods=['GET'])
def get_paper_orders():
    """Get paper trading orders (pending and history)."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        result = paper_trading_manager.get_paper_orders()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting paper orders: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/stats', methods=['GET'])
def get_paper_stats():
    """Get paper trading performance statistics."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        result = paper_trading_manager.get_paper_stats()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting paper stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/paper-trading/reset', methods=['POST'])
def reset_paper_portfolio():
    """Reset paper trading portfolio to initial state."""
    try:
        if not PAPER_TRADING_AVAILABLE:
            return jsonify({'error': 'Paper trading not available'}), 500
        
        result = paper_trading_manager.reset_paper_portfolio()
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error resetting paper portfolio: {e}")
        return jsonify({'error': str(e)}), 500

# =====================================
# END PAPER TRADING API ENDPOINTS
# =====================================


if __name__ == '__main__':
    import os
    
    # Set environment variables if not already set
    if not os.getenv('DHAN_CLIENT_ID'):
        os.environ['DHAN_CLIENT_ID'] = '1107931059'
    if not os.getenv('DHAN_ACCESS_TOKEN'):
        os.environ['DHAN_ACCESS_TOKEN'] = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzU2ODMzMDc4LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwNzkzMTA1OSJ9.nmlNncCNvmF3hg43EF38SqP1gVAWdNkinSewYWQAlF4lpPo6i02tqMr_irAFA0z52a6u346w'
    
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'  # Allow external connections in production
    
    logger.info("Starting Dhan Advanced Algo Trading Backend...")
    logger.info(f"Market Scanner Manager initialized: {market_scanner_manager.get_scanner_status()}")
    print(f"🚀 Starting server on {host}:{port}")
    
    app.run(
        host=host,
        port=port,
        debug=True
    ) 