# Market Scanner Stock Universe Configuration

## Overview

The Market Scanner now supports scanning up to **174+ stocks** by default (increased from 53), with full customization options for different trading strategies and market coverage preferences.

## Current Default Universe (174 stocks)

The default stock universe includes:
- **NIFTY 50 stocks** - Top 50 large-cap stocks
- **BANKNIFTY constituents** - Banking sector stocks  
- **NIFTY NEXT 50** - Additional high-quality mid/large-cap stocks
- **Sector diversification** - PSU, IT, Pharma, Auto, Metals, Chemicals, Infrastructure
- **High liquidity focus** - Stocks with good trading volumes

## Why 174 Stocks?

1. **Performance Balance**: More stocks = more opportunities, but also more processing time
2. **Quality over Quantity**: Focus on liquid, reliable stocks with good data availability
3. **API Rate Limits**: Respects Dhan API limits while maximizing coverage
4. **Resource Efficiency**: Balances opportunity detection with system performance

## Customizing Your Stock Universe

### Method 1: Using Configuration (Recommended)

Create a custom configuration in your `config.py`:

```python
from dhan_advanced_algo.stock_universe_config import BANKING_UNIVERSE, IT_UNIVERSE

# Example: Scan only banking stocks
market_scanner_config = MarketScannerConfig(
    stock_universe=BANKING_UNIVERSE,  # Only 18 banking stocks
    scan_interval_seconds=60,  # Faster scanning for smaller universe
    max_concurrent_stocks=18
)
```

### Method 2: Using Predefined Universes

Available predefined universes in `stock_universe_config.py`:

```python
# Sector-specific (focused scanning)
BANKING_UNIVERSE          # 18 banking stocks
IT_UNIVERSE              # 16 IT/tech stocks  
PHARMA_UNIVERSE          # 17 pharmaceutical stocks
AUTO_UNIVERSE            # 15 automotive stocks

# Size-based (risk/coverage preference)
CONSERVATIVE_UNIVERSE    # 50 NIFTY stocks (stable, high liquidity)
AGGRESSIVE_UNIVERSE      # 300+ NIFTY 500 stocks (maximum coverage)

# Strategy-based (trading style)
INTRADAY_UNIVERSE        # 20 high-volume stocks (day trading)
SWING_UNIVERSE           # 50 NIFTY stocks (swing trading)
POSITIONAL_UNIVERSE      # 300+ stocks (long-term positions)
```

### Method 3: Custom Stock List

Define your own universe:

```python
# Custom list example
CUSTOM_UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "SBIN", "BHARTIARTL", "AXISBANK", "ITC", "MARUTI"
]

market_scanner_config = MarketScannerConfig(
    stock_universe=CUSTOM_UNIVERSE
)
```

## Performance Considerations

### Stock Count vs Performance

| Universe Size | Scan Time | Memory Usage | Opportunities | Best For |
|---------------|-----------|--------------|---------------|----------|
| 20-50 stocks | ~30 seconds | Low | Medium | Intraday trading |
| 50-100 stocks | ~60 seconds | Medium | Good | Swing trading |
| 100-200 stocks | ~90 seconds | Medium-High | High | Positional trading |
| 200+ stocks | ~120+ seconds | High | Very High | Comprehensive scanning |

### Optimization Tips

1. **Start Small**: Begin with 50-100 stocks and scale up based on performance
2. **Sector Focus**: Use sector-specific universes for targeted strategies
3. **Time-based**: Use larger universes during less active hours
4. **Strategy Alignment**: Match universe size to your trading style

## Configuration Examples

### Conservative Day Trader
```python
# Focus on high-liquidity NIFTY 50 stocks
stock_universe = CONSERVATIVE_UNIVERSE
scan_interval_seconds = 60  # Scan every minute
max_concurrent_stocks = 20
```

### Aggressive Swing Trader  
```python
# Scan broader market for swing opportunities
stock_universe = AGGRESSIVE_UNIVERSE  
scan_interval_seconds = 300  # Scan every 5 minutes
max_concurrent_stocks = 50
```

### Sector Specialist (Banking)
```python
# Deep focus on banking sector
stock_universe = BANKING_UNIVERSE
scan_interval_seconds = 30  # Very frequent scanning
max_concurrent_stocks = 18
```

## API and Performance Impact

### Current API Usage
- **Default (174 stocks)**: ~174 API calls per scan cycle
- **Scan frequency**: Every 5 minutes (configurable)
- **Daily API calls**: ~50,000 calls (within Dhan limits)

### Scaling Considerations
- **500+ stocks**: Consider increasing scan intervals to avoid rate limits
- **1000+ stocks**: May require API call batching and longer intervals
- **Custom filtering**: Pre-filter stocks based on volume/price criteria

## Monitoring and Adjustments

### Key Metrics to Track
1. **Scan completion time** - Should be under 2 minutes
2. **Opportunities found** - Target 5-15 opportunities per scan  
3. **API success rate** - Should be >95%
4. **Memory usage** - Monitor for memory leaks with large universes

### Dynamic Adjustments
The system automatically:
- Skips invalid/suspended stocks
- Adjusts batch sizes based on response times
- Falls back to smaller universe on errors
- Logs performance metrics for optimization

## Getting Started

1. **Test with default universe** (174 stocks) - works out of the box
2. **Monitor performance** for 1-2 days
3. **Adjust based on your needs**:
   - Too slow? → Use smaller universe
   - Missing opportunities? → Expand universe  
   - Sector focus? → Use sector-specific universe
4. **Fine-tune parameters** like scan intervals and concurrent limits

The expanded stock universe provides significantly more trading opportunities while maintaining system performance and reliability. 