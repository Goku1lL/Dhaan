# Stock Universe Selector - User Guide

## Overview

The Market Scanner now includes a **configurable frontend dropdown** that allows you to switch between different stock universes in real-time. This gives you complete control over which stocks to scan without touching any code.

![Universe Selector](https://via.placeholder.com/800x200/2196F3/FFFFFF?text=Stock+Universe+Selector+Dropdown)

## How to Use

### 1. **Quick Universe Selection**
- In the Market Scanner page, look for the **"Stock Universe"** dropdown in the top-right corner
- Select any universe from the dropdown 
- The scanner will **automatically update** and start scanning the new universe
- You'll see the stock count change immediately

### 2. **Advanced Universe Configuration**
- Click the **Settings (⚙️) button** next to the dropdown
- A detailed dialog opens showing all available universes
- Each universe shows:
  - **Name and stock count**
  - **Category** (Sector, Strategy, etc.)
  - **Description** of what it covers
  - **Color-coded categories**

### 3. **Real-time Updates**
- Changes take effect **immediately**
- Stock count updates in real-time
- No need to restart the scanner
- Current scan results reflect the new universe

## Available Universes

### 📊 **Balanced Options**
- **Default (184 stocks)** - Balanced universe with NIFTY 50, NEXT 50, and sector leaders

### 🛡️ **Conservative Options** 
- **Conservative (50 stocks)** - NIFTY 50 stocks - high liquidity, stable companies

### 🚀 **Aggressive Options**
- **Aggressive (262 stocks)** - NIFTY 500 universe - maximum market coverage

### 🏢 **Sector-Specific**
- **Banking Sector (18 stocks)** - Banking and financial services only
- **IT Sector (16 stocks)** - Information Technology and software companies  
- **Pharmaceutical Sector (17 stocks)** - Pharmaceutical and healthcare companies
- **Automotive Sector (15 stocks)** - Automotive and auto ancillary companies

### 📈 **Strategy-Based**
- **Intraday Trading (20 stocks)** - High-volume, liquid stocks ideal for day trading
- **Swing Trading (50 stocks)** - NIFTY 50 stocks suitable for swing trading
- **Positional Trading (262 stocks)** - Comprehensive universe for long-term positions

## Best Practices

### **Choose Based on Your Trading Style**

#### 🔥 **Day Trading**
- Use **"Intraday Trading"** (20 stocks)
- High liquidity, fast moving stocks
- Quick scans, frequent opportunities

#### 📊 **Swing Trading** 
- Use **"Swing Trading"** or **"Conservative"** (50 stocks)
- Stable, well-established companies
- Medium-term opportunities

#### 📈 **Positional Trading**
- Use **"Aggressive"** or **"Positional"** (262 stocks)
- Maximum market coverage
- Long-term opportunity discovery

#### 🎯 **Sector Focus**
- Use specific **sector universes** (15-18 stocks each)
- Deep focus on particular industries
- Specialized sector strategies

### **Performance Considerations**

| Universe Size | Scan Time | Best For |
|---------------|-----------|----------|
| 15-20 stocks | ~30 seconds | Intraday, sector focus |
| 50 stocks | ~60 seconds | Swing trading, conservative |
| 100+ stocks | ~90+ seconds | Comprehensive scanning |
| 250+ stocks | ~120+ seconds | Maximum opportunity hunting |

### **Dynamic Switching**

1. **Start Conservative** - Begin with 50-stock universes to test strategies
2. **Scale Up** - Move to larger universes as performance allows
3. **Sector Rotation** - Switch to sector-specific universes based on market conditions
4. **Time-based** - Use smaller universes during active trading hours

## Technical Features

### **Real-time Updates**
- ✅ No server restart required
- ✅ Instant stock count changes
- ✅ Immediate scan result updates
- ✅ Automatic universe persistence

### **Smart Validation**
- ✅ Prevents invalid universe selections
- ✅ Shows current universe status
- ✅ Handles errors gracefully
- ✅ Provides detailed feedback

### **Visual Indicators**
- 🎨 **Color-coded categories** (Sector, Strategy, etc.)
- 📊 **Real-time stock counts** 
- ⚡ **Status indicators** (Loading, Active, etc.)
- 📋 **Sample stock previews**

## Troubleshooting

### **Universe Not Changing?**
- Ensure scanner is not currently running
- Check browser console for errors
- Try refreshing the page

### **Performance Issues?**
- Switch to smaller universes (20-50 stocks)
- Increase scan intervals in settings
- Monitor system resources

### **Missing Opportunities?**
- Try larger universes (100+ stocks)
- Switch to sector-specific if focusing on particular industries
- Ensure market hours for active scanning

## API Integration

For developers, the universe selection is also available via API:

```bash
# Get available universes
curl http://localhost:8000/api/market-scanner/universes

# Update universe
curl -X POST http://localhost:8000/api/market-scanner/universe \
  -H "Content-Type: application/json" \
  -d '{"universe_id": "banking"}'

# Get current universe
curl http://localhost:8000/api/market-scanner/universe
```

## Summary

The **Stock Universe Selector** gives you complete control over your market scanning scope with:

- ✅ **10 predefined universes** covering all major strategies and sectors
- ✅ **Real-time switching** without any downtime
- ✅ **Visual category organization** for easy selection
- ✅ **Performance optimization** for different trading styles
- ✅ **Seamless integration** with existing scanning functionality

**Result: You can now optimize your market scanning for any trading strategy or market condition with just a few clicks!** 🎯 