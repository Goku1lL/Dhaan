import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Trading API interface
export interface TradingAPI {
  // Dashboard APIs
  getDashboard: () => Promise<any>;
  getDashboardData: () => Promise<any>; // Alias for getDashboard
  
  // Position APIs
  getPositions: () => Promise<any>;
  closePosition: (positionId: string, closeForm: any) => Promise<any>;
  
  // Order APIs
  getOrders: () => Promise<any>;
  placeOrder: (orderForm: any) => Promise<any>;
  cancelOrder: (orderId: string) => Promise<any>;
  
  // Strategy APIs
  getStrategies: () => Promise<any>;
  createStrategy: (strategy: any) => Promise<any>;
  updateStrategy: (strategyId: string, strategy: any) => Promise<any>;
  deleteStrategy: (strategyId: string) => Promise<any>;
  
  // Market Data APIs
  getMarketSymbols: () => Promise<any>;
  
  // Analytics APIs (NEW)
  getPerformanceAnalytics: () => Promise<any>;
  getMarketOverview: () => Promise<any>;
  
  // Risk Management APIs
  getRiskMetrics: () => Promise<any>;
  getRiskSummary: () => Promise<any>;
  updateRiskLimits: (limits: any) => Promise<any>;
  
  // Market Scanner APIs
  getMarketScanResults: () => Promise<any>;
  startMarketScanning: () => Promise<any>;
  stopMarketScanning: () => Promise<any>;
  getScannerStatus: () => Promise<any>;
  getEODReport: (date?: string) => Promise<any>;
  
  // Stock Universe Management APIs
  getStockUniverses: () => Promise<any>;
  updateStockUniverse: (universeId: string) => Promise<any>;
  getCurrentUniverse: () => Promise<any>;
  
  // Strategy Management APIs
  enableStrategy: (strategyId: string) => Promise<any>;
  disableStrategy: (strategyId: string) => Promise<any>;

  // Paper Trading APIs
  getTradingMode: () => Promise<any>;
  setTradingMode: (mode: string) => Promise<any>;
  placePaperOrder: (orderData: any) => Promise<any>;
  cancelPaperOrder: (orderId: string) => Promise<any>;
  getPaperPortfolio: () => Promise<any>;
  getPaperPositions: () => Promise<any>;
  closePaperPosition: (symbol: string, quantity?: number) => Promise<any>;
  getPaperOrders: () => Promise<any>;
  getPaperStats: () => Promise<any>;
  resetPaperPortfolio: () => Promise<any>;
  
  // Strategy Paper Trading APIs
  getStrategyTradingStatus: () => Promise<any>;
  enableStrategyAutoTrading: () => Promise<any>;
  disableStrategyAutoTrading: () => Promise<any>;
  processStrategyOpportunities: () => Promise<any>;
  getStrategyPerformance: () => Promise<any>;
  getStrategyActiveTrades: () => Promise<any>;
}

// Implementation of Trading API
export const tradingAPI: TradingAPI = {
  // Dashboard
  getDashboard: () => api.get('/api/dashboard'),
  getDashboardData: () => api.get('/api/dashboard'), // Alias for getDashboard
  
  // Positions
  getPositions: () => api.get('/api/positions'),
  closePosition: (positionId: string, closeForm: any) => api.post(`/api/positions/${positionId}/close`, closeForm),
  
  // Orders
  getOrders: () => api.get('/api/orders'),
  placeOrder: (orderForm: any) => api.post('/api/orders', orderForm),
  cancelOrder: (orderId: string) => api.post(`/api/orders/${orderId}/cancel`),
  
  // Strategies
  getStrategies: () => api.get('/api/strategies'),
  createStrategy: (strategy: any) => api.post('/api/strategies', strategy),
  updateStrategy: (strategyId: string, strategy: any) => api.put(`/api/strategies/${strategyId}`, strategy),
  deleteStrategy: (strategyId: string) => api.delete(`/api/strategies/${strategyId}`),
  
  // Market Data
  getMarketSymbols: () => api.get('/api/market-symbols'),
  
  // Analytics
  getPerformanceAnalytics: () => api.get('/api/analytics/performance'),
  getMarketOverview: () => api.get('/api/analytics/market-overview'),
  
  // Risk Management
  getRiskMetrics: () => api.get('/api/risk/metrics'),
  getRiskSummary: () => api.get('/api/risk/summary'),
  updateRiskLimits: (limits: any) => api.post('/api/risk/limits', limits),
  
  // Market Scanner APIs
  getMarketScanResults: () => api.get('/api/market-scanner/scan-results'),
  startMarketScanning: () => api.post('/api/market-scanner/start'),
  stopMarketScanning: () => api.post('/api/market-scanner/stop'),
  getScannerStatus: () => api.get('/api/market-scanner/status'),
  getEODReport: (date?: string) => api.get('/api/market-scanner/eod-report', { params: date ? { date } : {} }),
  
  // Stock Universe Management APIs
  getStockUniverses: () => api.get('/api/market-scanner/universes'),
  updateStockUniverse: (universeId: string) => api.post('/api/market-scanner/universe', { universe_id: universeId }),
  getCurrentUniverse: () => api.get('/api/market-scanner/universe'),
  
  // Strategy Management APIs
  enableStrategy: (strategyId: string) => api.post(`/api/strategies/${strategyId}/enable`),
  disableStrategy: (strategyId: string) => api.post(`/api/strategies/${strategyId}/disable`),

  // Paper Trading APIs
  getTradingMode: () => api.get('/api/paper-trading/mode'),
  setTradingMode: (mode: string) => api.post('/api/paper-trading/mode', { mode }),
  placePaperOrder: (orderData: any) => api.post('/api/paper-trading/orders', orderData),
  cancelPaperOrder: (orderId: string) => api.post(`/api/paper-trading/orders/${orderId}/cancel`),
  getPaperPortfolio: () => api.get('/api/paper-trading/portfolio'),
  getPaperPositions: () => api.get('/api/paper-trading/positions'),
  closePaperPosition: (symbol: string, quantity?: number) => api.post(`/api/paper-trading/positions/${symbol}/close`, { quantity }),
  getPaperOrders: () => api.get('/api/paper-trading/orders'),
  getPaperStats: () => api.get('/api/paper-trading/stats'),
  resetPaperPortfolio: () => api.post('/api/paper-trading/reset'),
  
  // Strategy Paper Trading APIs
  getStrategyTradingStatus: () => api.get('/api/strategy-trading/status'),
  enableStrategyAutoTrading: () => api.post('/api/strategy-trading/auto-trading/enable'),
  disableStrategyAutoTrading: () => api.post('/api/strategy-trading/auto-trading/disable'),
  processStrategyOpportunities: () => api.post('/api/strategy-trading/process-opportunities'),
  getStrategyPerformance: () => api.get('/api/strategy-trading/performance'),
  getStrategyActiveTrades: () => api.get('/api/strategy-trading/active-trades'),
};

// Error interceptor for handling API errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    if (error.response) {
      // Server responded with error status
      console.error('Error response:', error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received:', error.request);
    } else {
      // Something else happened
      console.error('Error message:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api; 