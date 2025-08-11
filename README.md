# 🚀 Dhaan - Advanced Algorithmic Trading System

A comprehensive algorithmic trading system with **Integrated Strategy Paper Trading**, real-time market scanning, and automated strategy execution for Indian stock markets.

## ✨ **NEW: Integrated Strategy Paper Trading System**

🎯 **Test actual trading strategies with paper money before going live!**

- **Automated Strategy Execution**: Market scanner opportunities → Strategy decisions → Paper trades
- **8 Built-in Trading Strategies**: RSI, Momentum, Bollinger, Grid Trading, etc.  
- **Real-time Performance Analytics**: Win rates, P&L, drawdown analysis per strategy
- **Strategy Testing Dashboard**: Compare strategies side-by-side with comprehensive metrics
- **Risk Management**: Position sizing, confidence filtering, trade validation

📊 **See [STRATEGY_TESTING_SYSTEM.md](STRATEGY_TESTING_SYSTEM.md) for complete documentation**

---

## 🏗️ Original System Overview

A comprehensive algorithmic trading system with a modern React frontend and Python backend, designed for the Indian stock market.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  Flask Backend  │    │ Python Trading  │
│   (Dashboard)   │◄──►│   (API Layer)   │◄──►│   Engine Core   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
Dhaan/
├── frontend/                    # React TypeScript Frontend
│   ├── src/
│   │   ├── components/         # UI Components
│   │   ├── services/           # API Services
│   │   └── App.tsx            # Main App Component
│   ├── package.json
│   └── README.md
│
├── backend/                     # Flask API Backend
│   ├── app.py                  # Main Flask App
│   └── requirements.txt        # Python Dependencies
│
├── dhan_advanced_algo/         # Core Trading System
│   ├── core/                   # Core Abstractions
│   │   ├── interfaces.py       # Abstract Interfaces
│   │   ├── entities.py         # Domain Entities
│   │   ├── exceptions.py       # Custom Exceptions
│   │   └── trading_engine.py   # Trading Engine
│   ├── providers/              # Concrete Implementations
│   │   ├── risk_manager.py     # Risk Management
│   │   ├── position_manager.py # Position Management
│   │   ├── strategy_manager.py # Strategy Execution
│   │   └── notification_service.py # Notifications
│   └── __init__.py             # Package Exports
│
├── requirements.txt             # Python Dependencies
├── venv/                       # Virtual Environment
└── README.md                   # This File
```

## 🚀 Quick Start

### 1. Frontend Setup

```bash
cd frontend
npm install
npm start
```

The React app will open at `http://localhost:3030`

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The Flask API will run at `http://localhost:5000`

### 3. Core Trading System

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test imports
python -c "import dhan_advanced_algo; print('✅ Core system imported successfully!')"
```

## 🎯 Features

### Frontend Dashboard
- 📊 **Real-time Portfolio Overview** - Live P&L, positions, and risk metrics
- 📈 **Interactive Charts** - Portfolio performance and market data visualization
- 🎮 **Trading Controls** - Order placement, position management, strategy control
- ⚠️ **Risk Monitoring** - Real-time risk metrics and alerts
- 🔔 **Notifications** - Trade alerts and system notifications
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

### Backend API
- 🔌 **RESTful API** - Complete trading system endpoints
- 🔒 **Authentication** - JWT-based security
- 📊 **Data Management** - Positions, orders, strategies, and risk metrics
- 🚦 **System Control** - Trading pause/resume, emergency stop
- 📡 **Real-time Updates** - WebSocket support for live data

### Core Trading Engine
- 🧠 **Strategy Management** - Multi-strategy execution framework
- ⚖️ **Risk Management** - Position sizing, loss limits, exposure control
- 📊 **Position Management** - Lifecycle management and P&L tracking
- 📈 **Market Data** - Real-time price feeds and technical indicators
- 🔔 **Notifications** - Telegram integration for alerts
- 💾 **Data Persistence** - Trade history and performance analytics

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Material-UI (MUI)** for professional UI components
- **Recharts** for data visualization
- **Axios** for API communication
- **React Router** for navigation

### Backend
- **Flask** for API server
- **Flask-CORS** for cross-origin requests
- **Python 3.8+** compatibility

### Core System
- **Python 3.8+** with type hints
- **Pandas & NumPy** for data processing
- **Telepot** for Telegram notifications
- **Clean Architecture** principles

## 🔧 Configuration

### Environment Variables

Create `.env` files in respective directories:

**Frontend (.env)**
```env
REACT_APP_API_URL=http://localhost:5000
```

**Backend (.env)**
```env
FLASK_ENV=development
FLASK_DEBUG=1
```

### Trading System Configuration

Edit `dhan_advanced_algo/config.py`:
```python
# Risk Management
MAX_DAILY_LOSS = 50000
MAX_POSITION_SIZE = 100000
MAX_PORTFOLIO_EXPOSURE = 0.8

# Telegram Notifications
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"
```

## 📊 API Endpoints

### Dashboard
- `GET /api/dashboard` - Portfolio overview and metrics

### Positions
- `GET /api/positions` - List all positions
- `GET /api/positions/{id}` - Get specific position
- `POST /api/positions/{id}/close` - Close position

### Orders
- `GET /api/orders` - List all orders
- `POST /api/orders` - Place new order
- `DELETE /api/orders/{id}` - Cancel order

### Strategies
- `GET /api/strategies` - List all strategies
- `POST /api/strategies` - Create new strategy
- `PUT /api/strategies/{id}` - Update strategy
- `POST /api/strategies/{id}/enable` - Enable strategy
- `POST /api/strategies/{id}/disable` - Disable strategy

### Risk Management
- `GET /api/risk/metrics` - Current risk metrics
- `GET /api/risk/summary` - Risk summary
- `PUT /api/risk/limits` - Update risk limits

### System Control
- `GET /api/system/status` - System status
- `POST /api/system/pause` - Pause trading
- `POST /api/system/resume` - Resume trading
- `POST /api/system/emergency-stop` - Emergency stop

## 🧪 Testing

### Frontend Testing
```bash
cd frontend
npm test
```

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Core System Testing
```bash
# Test imports
python -c "from dhan_advanced_algo import RiskManager, PositionManager; print('✅ Core components imported!')"

# Test compilation
python -m py_compile dhan_advanced_algo/**/*.py
```

## 🚀 Deployment

### Production Build
```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🔒 Security Features

- **JWT Authentication** for API access
- **CORS Configuration** for secure cross-origin requests
- **Input Validation** and sanitization
- **Rate Limiting** for API endpoints
- **Secure Headers** configuration

## 📈 Performance Features

- **Real-time Updates** via WebSocket
- **Data Caching** for frequently accessed data
- **Optimized Queries** for large datasets
- **Background Processing** for heavy computations
- **Connection Pooling** for database operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the inline code comments and docstrings
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join the community discussions for help and ideas

## 🎉 Acknowledgments

- **Material-UI** for the beautiful React components
- **Flask** for the lightweight Python web framework
- **Dhan** for the trading platform integration
- **Open Source Community** for the amazing tools and libraries

---

**Happy Trading! 🚀📈** 