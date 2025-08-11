# 📊 Paper Trading System - Complete Guide

## 🎯 Overview

The **Paper Trading System** provides risk-free virtual trading to test strategies without real money. It simulates real market conditions with:

- ✅ **Virtual Portfolio** with ₹1 Lakh starting balance
- ✅ **Real Market Simulation** with slippage and commission
- ✅ **Complete Order Management** (Buy, Sell, Cancel)
- ✅ **Position Tracking** with P&L calculation
- ✅ **Performance Analytics** and statistics
- ✅ **Trading Mode Toggle** (Live/Paper switch)

---

## 🚀 **Getting Started**

### **1. Access Paper Trading**
- Navigate to **Paper Trading** in the sidebar
- Toggle **Trading Mode** to switch between LIVE and PAPER
- Default mode is **PAPER** for safety

### **2. Initial Setup**
- **Starting Balance**: ₹1,00,000 virtual money
- **Commission**: ₹20 per trade (configurable)
- **Slippage**: 0.1% on market orders (realistic simulation)
- **Margin**: 20% requirement for positions

---

## 🎮 **Using the Paper Trading Dashboard**

### **📈 Portfolio Summary Cards**
```
┌─────────────────┬──────────────────┬─────────────────┬─────────────────┐
│ Portfolio Value │ Available Cash   │ Total P&L       │ Win Rate        │
│ ₹1,00,000      │ ₹90,000         │ +₹5,000 (5%)   │ 75% (3/4)      │
└─────────────────┴──────────────────┴─────────────────┴─────────────────┘
```

### **📋 Four Main Tabs**

#### **1. Positions Tab**
- View all open positions
- Real-time P&L calculation
- Close positions (full or partial)
- Entry price, current price, unrealized P&L

#### **2. Pending Orders Tab**
- View submitted orders awaiting execution
- Cancel pending orders
- Order status tracking

#### **3. Order History Tab**
- Complete trading history
- Executed prices and times
- Order status progression

#### **4. Statistics Tab**
- Detailed performance metrics
- Win/loss ratios
- Drawdown analysis
- Commission tracking

---

## 💼 **Trading Operations**

### **🛒 Placing Orders**

**Step 1: Click "Place Order" button**

**Step 2: Fill order form:**
```
Symbol:      RELIANCE
Side:        BUY / SELL
Order Type:  MARKET / LIMIT
Quantity:    10
Price:       ₹2,500
```

**Step 3: Order executed with realistic simulation:**
- **Market Orders**: Immediate execution with slippage
- **Limit Orders**: Execute when price reaches limit
- **Commission**: ₹20 automatically deducted

### **📊 Position Management**

**View Positions:**
```
┌─────────┬──────────┬──────┬──────────────┬───────────────┬─────────────┐
│ Symbol  │ Quantity │ Side │ Entry Price  │ Current Price │ P&L         │
├─────────┼──────────┼──────┼──────────────┼───────────────┼─────────────┤
│ RELIANCE│ 10       │ BUY  │ ₹2,500      │ ₹2,520       │ +₹180       │
│ TCS     │ 5        │ BUY  │ ₹3,200      │ ₹3,180       │ -₹120       │
└─────────┴──────────┴──────┴──────────────┴───────────────┴─────────────┘
```

**Close Positions:**
- Full position: Leave quantity blank
- Partial: Specify quantity to close
- Automatic P&L calculation and commission

---

## 🎯 **API Endpoints**

### **Trading Mode Management**
```bash
# Get current trading mode
GET /api/paper-trading/mode

# Set trading mode
POST /api/paper-trading/mode
{"mode": "PAPER"}  # or "LIVE"
```

### **Order Management**
```bash
# Place order
POST /api/paper-trading/orders
{
  "symbol": "RELIANCE",
  "side": "BUY",
  "quantity": 10,
  "price": 2500,
  "order_type": "MARKET"
}

# Cancel order
POST /api/paper-trading/orders/{order_id}/cancel

# Get orders
GET /api/paper-trading/orders
```

### **Portfolio Management**
```bash
# Get portfolio summary
GET /api/paper-trading/portfolio

# Get positions
GET /api/paper-trading/positions

# Close position
POST /api/paper-trading/positions/{symbol}/close
{"quantity": 5}  # Optional - omit for full close

# Get performance stats
GET /api/paper-trading/stats

# Reset portfolio
POST /api/paper-trading/reset
```

---

## 📊 **Example Trading Session**

### **1. Start Trading**
```bash
curl http://localhost:8000/api/paper-trading/mode
# Response: {"trading_mode": "PAPER", "is_paper_mode": true, "paper_balance": 100000.0}
```

### **2. Place Buy Order**
```bash
curl -X POST http://localhost:8000/api/paper-trading/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "side": "BUY", "quantity": 10, "price": 2500}'

# Response: {
#   "success": true,
#   "virtual_order_id": "PAPER_12345678",
#   "price": 2502.5,  # Slippage applied
#   "status": "EXECUTED"
# }
```

### **3. Check Portfolio**
```bash
curl http://localhost:8000/api/paper-trading/portfolio

# Response: {
#   "account_balance": {
#     "available_margin": 95000.0,
#     "total_margin": 74980.0,
#     "realized_pnl": -25020.0
#   },
#   "positions": [{
#     "symbol": "RELIANCE",
#     "quantity": 10,
#     "entry_price": 2502.5,
#     "unrealized_pnl": -20.0
#   }]
# }
```

### **4. Close Position**
```bash
curl -X POST http://localhost:8000/api/paper-trading/positions/RELIANCE/close \
  -H "Content-Type: application/json" \
  -d '{"quantity": 5}'  # Partial close

# Closes 5 shares, keeps 5 open
```

### **5. Reset for New Session**
```bash
curl -X POST http://localhost:8000/api/paper-trading/reset

# Response: {
#   "success": true,
#   "final_stats": {...},
#   "new_balance": 100000.0
# }
```

---

## 🔧 **Configuration**

### **Core Configuration** (`dhan_advanced_algo/core/config.py`)
```python
@dataclass
class TradingConfig:
    # Paper Trading Configuration
    trading_mode: str = "PAPER"  # PAPER or LIVE
    paper_trading_balance: Decimal = Decimal('100000')  # ₹1 Lakh
    paper_trading_commission: Decimal = Decimal('20')   # ₹20 per trade
    paper_trading_slippage: float = 0.001              # 0.1% slippage
```

### **Customization Options**
- **Starting Balance**: Change `paper_trading_balance`
- **Commission Structure**: Modify `paper_trading_commission`
- **Slippage Simulation**: Adjust `paper_trading_slippage`
- **Margin Requirements**: Configure in PaperTradingBrokerProvider

---

## 📈 **Performance Analytics**

### **Key Metrics Tracked**
- **Portfolio Value**: Current total value
- **P&L**: Realized and unrealized gains/losses
- **Win Rate**: Percentage of profitable trades
- **Trade Count**: Total executed trades
- **Commission**: Total fees paid
- **Max Drawdown**: Peak-to-trough decline
- **Return %**: Overall portfolio performance

### **Statistical Analysis**
```python
# Example stats response
{
  "initial_balance": 100000.0,
  "current_balance": 105000.0,
  "total_return_pct": 5.0,
  "total_trades": 12,
  "winning_trades": 9,
  "losing_trades": 3,
  "win_rate": 75.0,
  "max_drawdown": 2500.0,
  "max_drawdown_pct": 2.5
}
```

---

## 🔄 **Trading Mode Switch**

### **PAPER Mode** (Default)
- ✅ Risk-free virtual trading
- ✅ Full feature simulation
- ✅ Performance tracking
- ✅ Strategy testing

### **LIVE Mode**
- ⚠️ Real money trading
- ⚠️ Actual broker integration
- ⚠️ Real P&L impact
- ⚠️ Requires real API credentials

### **Switching Modes**
```typescript
// Frontend toggle
const toggleTradingMode = async () => {
  const newMode = isPaperMode ? 'LIVE' : 'PAPER';
  await tradingAPI.setTradingMode(newMode);
};
```

---

## 🛡️ **Safety Features**

### **Risk Protection**
- **Default Paper Mode**: System starts in PAPER mode
- **Clear Mode Indicators**: Visual indicators show current mode
- **Confirmation Dialogs**: For critical operations
- **Portfolio Reset**: Easy restart capability

### **Realistic Simulation**
- **Market Slippage**: 0.1% price impact on market orders
- **Commission Costs**: ₹20 per trade deduction
- **Margin Requirements**: 20% margin for positions
- **Immediate Execution**: Orders execute instantly for testing

---

## 🔧 **Technical Architecture**

### **Backend Components**
```
PaperTradingManager
├── PaperTradingBrokerProvider (ITradingBroker)
├── VirtualPosition (Position tracking)
├── Order execution simulation
└── Performance statistics

API Endpoints
├── /api/paper-trading/mode
├── /api/paper-trading/orders
├── /api/paper-trading/portfolio
├── /api/paper-trading/positions
└── /api/paper-trading/stats
```

### **Frontend Components**
```
PaperTrading.tsx
├── Portfolio Summary Cards
├── Order Placement Dialog
├── Position Management Table
├── Statistics Dashboard
└── Trading Mode Toggle
```

---

## 🎯 **Best Practices**

### **For Strategy Testing**
1. **Start with Paper Trading** - Always test strategies risk-free first
2. **Use Realistic Amounts** - Trade with amounts you'd use live
3. **Track Performance** - Monitor win rates and drawdowns
4. **Test Edge Cases** - Try various market conditions
5. **Document Results** - Keep records of what works

### **For Learning**
1. **Experiment Freely** - Paper trading allows unlimited experimentation
2. **Try Different Styles** - Test day trading, swing trading, etc.
3. **Learn Order Types** - Practice with market and limit orders
4. **Understand P&L** - See how commission and slippage affect profits
5. **Use Reset Feature** - Start fresh when needed

---

## 🚀 **Next Steps**

### **After Mastering Paper Trading**
1. **Analyze Performance** - Review statistics and improve strategies
2. **Gradual Live Trading** - Start with small amounts in live mode
3. **Strategy Refinement** - Use insights to improve algorithms
4. **Risk Management** - Apply lessons learned to live trading

### **Advanced Features** (Future Enhancements)
- Historical backtesting
- Multiple portfolio simulation
- Advanced order types
- Real-time market data integration
- Strategy performance comparison

---

**🎯 The Paper Trading System provides a complete, risk-free environment to develop and test trading strategies. Master it here before moving to live trading!**

---

## 📞 **Support**

- **Documentation**: This guide covers all features
- **API Reference**: See endpoint documentation above
- **Configuration**: Check `dhan_advanced_algo/core/config.py`
- **Frontend**: Navigate to **Paper Trading** in the sidebar

**Happy Paper Trading! 📈✨** 