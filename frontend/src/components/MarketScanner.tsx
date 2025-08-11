import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  IconButton,
  Tooltip,
  Badge,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  LinearProgress
} from '@mui/material';
import {
  Refresh,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  PlayArrow,
  Stop,
  Visibility,
  Warning,
  CheckCircle,
  Error,
  Settings,
  Info,
  AccountBalance,
  Computer,
  LocalHospital,
  DriveEta,
  TrendingUp as TrendingUpIcon,
  SwapHoriz,
  ShowChart
} from '@mui/icons-material';
import { tradingAPI } from '../services/api';

interface TradingOpportunity {
  id: string;
  symbol: string;
  strategy_name: string;
  strategy_id: string;
  signal_type: 'BUY' | 'SELL' | 'SHORT';
  confidence_score: number;
  entry_price: number;
  target_price: number;
  stop_loss: number;
  risk_reward_ratio: number;
  volume: number;
  timestamp: string;
  indicators: Record<string, any>;
  description: string;
}

interface MarketScanResult {
  scan_timestamp: string;
  total_stocks_scanned: number;
  opportunities_found: number;
  opportunities: TradingOpportunity[];
  scan_duration: number;
  market_sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
}

interface StockUniverse {
  id: string;
  name: string;
  description: string;
  stock_count: number;
  category: string;
}

interface CurrentUniverse {
  universe_id: string;
  universe_name: string;
  stock_count: number;
  stocks: string[];
}

const MarketScanner: React.FC = () => {
  const [scanResults, setScanResults] = useState<MarketScanResult | null>(null);
  const [opportunities, setOpportunities] = useState<TradingOpportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [lastScanTime, setLastScanTime] = useState<string | null>(null);

  // Universe management state
  const [availableUniverses, setAvailableUniverses] = useState<StockUniverse[]>([]);
  const [currentUniverse, setCurrentUniverse] = useState<CurrentUniverse | null>(null);
  const [selectedUniverseId, setSelectedUniverseId] = useState<string>('default');
  const [universeDialogOpen, setUniverseDialogOpen] = useState(false);
  const [universeLoading, setUniverseLoading] = useState(false);

  // Scanning progress and timer state
  const [scanStartTime, setScanStartTime] = useState<number | null>(null);
  const [scanElapsedTime, setScanElapsedTime] = useState<number>(0);
  const [scanProgress, setScanProgress] = useState<number>(0);
  const [stocksProcessed, setStocksProcessed] = useState<number>(0);
  const [nextScanCountdown, setNextScanCountdown] = useState<number>(0);
  const [scanStatus, setScanStatus] = useState<string>('idle'); // 'idle', 'scanning', 'waiting'

  // Check scanner status on mount
  useEffect(() => {
    fetchMarketScanResults();
    checkScannerStatus();
    loadAvailableUniverses();
    loadCurrentUniverse();
    // Set up auto-refresh every 5 minutes
    const interval = setInterval(fetchMarketScanResults, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Timer management for scanning progress
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (isScanning && scanStartTime) {
      interval = setInterval(() => {
        const elapsed = Date.now() - scanStartTime;
        setScanElapsedTime(elapsed);
        
        // Scanning timeout - if scanning for more than 10 minutes, stop it
        if (elapsed > 600000) { // 10 minutes in milliseconds
          console.warn('Scanning timeout reached (10 minutes), stopping scanner...');
          setError('Scanning timeout reached. Stopping scanner...');
          stopScanning();
          return;
        }
        
        // Estimate progress based on elapsed time (assume 2-3 minutes for large scans)
        const totalStocks = currentUniverse?.stock_count || 184;
        const estimatedDuration = totalStocks * 500; // 500ms per stock (estimated)
        const progress = Math.min((elapsed / estimatedDuration) * 100, 95); // Cap at 95% until real completion
        setScanProgress(progress);
        
        // Estimate stocks processed
        const processed = Math.min(Math.floor((elapsed / 500)), totalStocks);
        setStocksProcessed(processed);
      }, 1000);
    } else if (!isScanning) {
      setScanElapsedTime(0);
      setScanProgress(0);
      setStocksProcessed(0);
      setScanStartTime(null);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isScanning, scanStartTime, currentUniverse?.stock_count]);

  // Countdown timer for next scan (when scanner is running but waiting)
  useEffect(() => {
    let countdownInterval: NodeJS.Timeout | null = null;
    
    if (isScanning && scanStatus === 'waiting' && nextScanCountdown > 0) {
      countdownInterval = setInterval(() => {
        setNextScanCountdown(prev => {
          if (prev <= 1) {
            setScanStatus('scanning');
            setScanStartTime(Date.now());
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (countdownInterval) clearInterval(countdownInterval);
    };
  }, [isScanning, scanStatus, nextScanCountdown]);

  const checkScannerStatus = async () => {
    try {
      const response = await tradingAPI.getScannerStatus();
      if (response.data) {
        setIsScanning(response.data.is_scanning || false);
      }
    } catch (error) {
      console.error('Error checking scanner status:', error);
    }
  };

  const fetchMarketScanResults = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use real API call instead of mock data
      const response = await tradingAPI.getMarketScanResults();
      
      if (response.data) {
        const scanResult: MarketScanResult = {
          scan_timestamp: response.data.scan_timestamp,
          total_stocks_scanned: response.data.total_stocks_scanned,
          opportunities_found: response.data.opportunities_found,
          opportunities: response.data.opportunities,
          scan_duration: response.data.scan_duration,
          market_sentiment: response.data.market_sentiment
        };
        
        setScanResults(scanResult);
        setOpportunities(scanResult.opportunities);
        setLastScanTime(scanResult.scan_timestamp);
        
        // Update scanner status and timer
        const isCurrentlyScanning = response.data.is_scanning || false;
        setIsScanning(isCurrentlyScanning);
        
        if (isCurrentlyScanning) {
          // Check if this is a new scan (recent scan timestamp indicates active scanning)
          const scanTime = new Date(response.data.scan_timestamp);
          const now = new Date();
          const timeDiff = (now.getTime() - scanTime.getTime()) / 1000;
          
          if (timeDiff < 60) { // If scan timestamp is within last minute, likely scanning
            setScanStatus('scanning');
            if (!scanStartTime) {
              setScanStartTime(Date.now() - (timeDiff * 1000)); // Adjust for elapsed time
            }
          } else {
            // Scanner is active but waiting for next scan
            setScanStatus('waiting');
            // Set countdown to next scan (5 minutes = 300 seconds)
            const nextScanIn = 300 - (timeDiff % 300);
            setNextScanCountdown(Math.max(0, nextScanIn));
          }
        } else {
          // Backend is not scanning - reset all scanning states
          setScanStatus('idle');
          setScanStartTime(null);
          setNextScanCountdown(0);
          setScanElapsedTime(0);
          setScanProgress(0);
          setStocksProcessed(0);
        }
      } else {
        setError('No data received from server');
        // Reset scanning state on error
        setIsScanning(false);
        setScanStatus('idle');
        setScanStartTime(null);
        setNextScanCountdown(0);
        setScanElapsedTime(0);
        setScanProgress(0);
        setStocksProcessed(0);
      }
    } catch (error) {
      console.error('Error fetching market scan results:', error);
      setError('Failed to connect to market scanner. Please check if the backend is running.');
      
      // Reset all scanning states on error
      setIsScanning(false);
      setScanStatus('idle');
      setScanStartTime(null);
      setNextScanCountdown(0);
      setScanElapsedTime(0);
      setScanProgress(0);
      setStocksProcessed(0);
    } finally {
      setLoading(false);
    }
  };

  const startScanning = async () => {
    try {
      setIsScanning(true);
      setError(null);
      
      // Initialize timer and progress
      setScanStatus('scanning');
      setScanStartTime(Date.now());
      setScanProgress(0);
      setStocksProcessed(0);
      setScanElapsedTime(0);
      
      // Call backend API to start scanning
      const response = await tradingAPI.startMarketScanning();
      
      if (response.data && response.data.status === 'success') {
        console.log('Market scanning started:', response.data.message);
        
        // Set up scan completion detection
        setTimeout(() => {
          fetchMarketScanResults();
          // After first scan completes, switch to waiting mode
          setScanStatus('waiting');
          setNextScanCountdown(300); // 5 minutes = 300 seconds
          setScanProgress(100);
        }, 2000);
      } else {
        setError(response.data?.message || 'Failed to start scanning');
        setIsScanning(false);
        setScanStatus('idle');
      }
      
    } catch (error) {
      console.error('Error starting market scan:', error);
      setError('Failed to start market scanning. Please try again.');
      setIsScanning(false);
      setScanStatus('idle');
    }
  };

  const stopScanning = async () => {
    try {
      setError(null);
      
      // Reset all timer states
      setScanStatus('idle');
      setScanStartTime(null);
      setScanProgress(0);
      setStocksProcessed(0);
      setScanElapsedTime(0);
      setNextScanCountdown(0);
      
      // Call backend API to stop scanning
      const response = await tradingAPI.stopMarketScanning();
      
      if (response.data && response.data.status === 'success') {
        console.log('Market scanning stopped:', response.data.message);
        setIsScanning(false);
      } else {
        setError(response.data?.message || 'Failed to stop scanning');
      }
      
    } catch (error) {
      console.error('Error stopping market scan:', error);
      setError('Failed to stop market scanning. Please try again.');
      // Still set to false since we attempted to stop
      setIsScanning(false);
    }
  };

  const loadAvailableUniverses = async () => {
    try {
      const response = await tradingAPI.getStockUniverses();
      if (response.data && response.data.universes) {
        setAvailableUniverses(response.data.universes);
      }
    } catch (error) {
      console.error('Error loading available universes:', error);
    }
  };

  const loadCurrentUniverse = async () => {
    try {
      const response = await tradingAPI.getCurrentUniverse();
      if (response.data) {
        setCurrentUniverse(response.data);
        setSelectedUniverseId(response.data.universe_id);
      }
    } catch (error) {
      console.error('Error loading current universe:', error);
    }
  };

  const updateUniverse = async (universeId: string) => {
    try {
      setUniverseLoading(true);
      
      const response = await tradingAPI.updateStockUniverse(universeId);
      if (response.data && response.data.status === 'success') {
        // Reload current universe and scan results
        await loadCurrentUniverse();
        await fetchMarketScanResults();
        
        setUniverseDialogOpen(false);
        setError(null);
      } else {
        setError(response.data?.message || 'Failed to update universe');
      }
    } catch (error) {
      console.error('Error updating universe:', error);
      setError('Failed to update stock universe. Please try again.');
    } finally {
      setUniverseLoading(false);
    }
  };

  const getSignalColor = (signalType: string) => {
    switch (signalType) {
      case 'BUY':
        return 'success';
      case 'SELL':
        return 'error';
      case 'SHORT':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getSignalIcon = (signalType: string) => {
    switch (signalType) {
      case 'BUY':
        return <TrendingUp />;
      case 'SELL':
        return <TrendingDown />;
      case 'SHORT':
        return <TrendingDown />;
      default:
        return <TrendingFlat />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const getMarketSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
        return 'success';
      case 'BEARISH':
        return 'error';
      case 'NEUTRAL':
        return 'info';
      default:
        return 'default';
    }
  };

  const getMarketSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'BULLISH':
        return <TrendingUp />;
      case 'BEARISH':
        return <TrendingDown />;
      case 'NEUTRAL':
        return <TrendingFlat />;
      default:
        return <TrendingFlat />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'sector':
        return <AccountBalance />;
      case 'strategy':
        return <ShowChart />;
      case 'aggressive':
        return <TrendingUpIcon />;
      case 'conservative':
        return <SwapHoriz />;
      default:
        return <Info />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'sector':
        return '#2196f3';
      case 'strategy': 
        return '#4caf50';
      case 'aggressive':
        return '#f44336';
      case 'conservative':
        return '#ff9800';
      default:
        return '#9e9e9e';
    }
  };

  // Utility functions for timer and progress
  const formatTime = (milliseconds: number): string => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  const formatCountdown = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `0:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getScanStatusText = (): string => {
    if (!isScanning) return 'Scanner Idle';
    
    switch (scanStatus) {
      case 'scanning':
        return `Scanning... (${stocksProcessed}/${currentUniverse?.stock_count || 0} stocks)`;
      case 'waiting':
        return `Next scan in ${formatCountdown(nextScanCountdown)}`;
      default:
        return 'Scanner Active';
    }
  };

  const getScanStatusColor = (): string => {
    if (!isScanning) return '#9e9e9e';
    
    switch (scanStatus) {
      case 'scanning':
        return '#4caf50';
      case 'waiting':
        return '#ff9800';
      default:
        return '#2196f3';
    }
  };

  const resetScannerState = () => {
    setIsScanning(false);
    setScanStatus('idle');
    setScanStartTime(null);
    setScanProgress(0);
    setStocksProcessed(0);
    setScanElapsedTime(0);
    setNextScanCountdown(0);
    setError(null);
  };

  const refreshData = async () => {
    try {
      setError(null);
      
      // If scanner appears to be stuck (scanning for more than 10 minutes), reset state
      if (isScanning && scanStartTime && (Date.now() - scanStartTime) > 600000) {
        console.warn('Scanner appears stuck, resetting state...');
        resetScannerState();
      }
      
      await fetchMarketScanResults();
    } catch (error) {
      console.error('Error refreshing data:', error);
      setError('Failed to refresh data. Please try again.');
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h4" gutterBottom>
            Market Scanner
          </Typography>
          {isScanning && scanStatus === 'scanning' && (
            <Chip 
              icon={<CircularProgress size={14} color="inherit" />}
              label="Scanning"
              size="small"
              color="primary"
              variant="outlined"
              sx={{ 
                height: 24,
                fontSize: '0.75rem',
                '& .MuiChip-icon': {
                  fontSize: 14
                }
              }}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {/* Universe Selector */}
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Stock Universe</InputLabel>
            <Select
              value={selectedUniverseId}
              label="Stock Universe"
              onChange={(e) => updateUniverse(e.target.value as string)}
              disabled={isScanning || universeLoading}
              sx={{ 
                backgroundColor: 'background.paper',
                '& .MuiSelect-select': {
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }
              }}
            >
              {availableUniverses.map((universe) => (
                <MenuItem key={universe.id} value={universe.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getCategoryIcon(universe.category)}
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {universe.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {universe.stock_count} stocks
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Universe Settings Button */}
          <Tooltip title="Configure Stock Universe">
            <IconButton 
              onClick={() => setUniverseDialogOpen(true)}
              disabled={universeLoading}
              sx={{ 
                backgroundColor: 'primary.main',
                color: 'white',
                '&:hover': { backgroundColor: 'primary.dark' }
              }}
            >
              <Settings />
            </IconButton>
          </Tooltip>

          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={refreshData}
            disabled={loading}
          >
            REFRESH
          </Button>
          {!isScanning ? (
            <Button
              variant="contained"
              color="success"
              startIcon={<PlayArrow />}
              onClick={startScanning}
              disabled={loading}
            >
              START SCANNING
            </Button>
          ) : (
            <Button
              variant="contained"
              color="error"
              startIcon={<Stop />}
              onClick={stopScanning}
            >
              STOP SCANNING
            </Button>
          )}
        </Box>
      </Box>

      {/* Market Overview */}
      {scanResults && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Stocks Scanned
                </Typography>
                <Typography variant="h4">
                  {scanResults.total_stocks_scanned.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Opportunities Found
                </Typography>
                <Typography variant="h4" color="primary">
                  {scanResults.opportunities_found}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Market Sentiment
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getMarketSentimentIcon(scanResults.market_sentiment)}
                  <Chip
                    label={scanResults.market_sentiment}
                    color={getMarketSentimentColor(scanResults.market_sentiment)}
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {isScanning ? 'Scan Status' : 'Last Scan'}
                </Typography>
                
                {isScanning ? (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {scanStatus === 'scanning' ? (
                        <>
                          <CircularProgress size={16} color="primary" />
                          <Typography variant="h6" color="primary.main" sx={{ fontWeight: 600 }}>
                            Scanning...
                          </Typography>
                        </>
                      ) : (
                        <>
                          <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
                          <Typography variant="h6" color="success.main" sx={{ fontWeight: 600 }}>
                            Active
                          </Typography>
                        </>
                      )}
                    </Box>
                    
                    {/* Progress Timer */}
                    <Box sx={{ mt: 1 }}>
                      {isScanning && (
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                          {scanStatus === 'scanning' && scanElapsedTime > 0 
                            ? `Elapsed: ${formatTime(scanElapsedTime)}`
                            : scanStatus === 'waiting' && nextScanCountdown > 0
                            ? `Next scan: ${formatCountdown(nextScanCountdown)}`
                            : scanStatus === 'scanning'
                            ? 'Starting scan...'
                            : scanStatus === 'waiting'
                            ? 'Preparing next scan...'
                            : 'Scanner running...'
                          }
                        </Typography>
                      )}
                      {!isScanning && (
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
                          Scanner inactive
                        </Typography>
                      )}
                    </Box>
                  </>
                ) : (
                  <>
                    <Typography variant="body2">
                      {lastScanTime ? new Date(lastScanTime).toLocaleTimeString() : 'Never'}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Duration: {scanResults.scan_duration.toFixed(1)}s
                    </Typography>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Compact Scanning Progress - Only during active scanning */}
      {isScanning && scanStatus === 'scanning' && (
        <Alert 
          severity="info" 
          sx={{ 
            mb: 2,
            backgroundColor: 'primary.light',
            color: 'primary.contrastText',
            '& .MuiAlert-icon': { color: 'inherit' }
          }}
          icon={<CircularProgress size={20} sx={{ color: 'inherit' }} />}
          action={
            <Chip 
              label={formatTime(scanElapsedTime)}
              size="small" 
              sx={{ 
                backgroundColor: 'rgba(255,255,255,0.2)', 
                color: 'inherit',
                fontWeight: 600
              }}
            />
          }
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              Scanning {currentUniverse?.universe_name || 'stocks'}... ({stocksProcessed}/{currentUniverse?.stock_count || 0})
            </Typography>
            
            {scanProgress > 0 && (
              <Box sx={{ width: 200, ml: 2 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={scanProgress} 
                  sx={{ 
                    height: 4, 
                    borderRadius: 2,
                    backgroundColor: 'rgba(255,255,255,0.3)',
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: 'white',
                      borderRadius: 2
                    }
                  }}
                />
                <Typography variant="caption" sx={{ color: 'inherit', opacity: 0.9, fontSize: '0.75rem' }}>
                  {scanProgress.toFixed(0)}% complete
                </Typography>
              </Box>
            )}
          </Box>
        </Alert>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
          <CircularProgress />
        </Box>
      ) : (
        /* Opportunities Table */
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Trading Opportunities
              </Typography>
              <Badge badgeContent={opportunities.length} color="primary">
                <Chip label="Live" color="success" size="small" />
              </Badge>
            </Box>
            
            {opportunities.length > 0 ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbol</TableCell>
                      <TableCell>Strategy</TableCell>
                      <TableCell>Signal</TableCell>
                      <TableCell>Confidence</TableCell>
                      <TableCell>Entry Price</TableCell>
                      <TableCell>Target</TableCell>
                      <TableCell>Stop Loss</TableCell>
                      <TableCell>Risk/Reward</TableCell>
                      <TableCell>Volume</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {opportunities.map((opportunity) => (
                      <TableRow key={opportunity.id} hover>
                        <TableCell>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {opportunity.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {opportunity.strategy_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getSignalIcon(opportunity.signal_type)}
                            label={opportunity.signal_type}
                            color={getSignalColor(opportunity.signal_type)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={`${(opportunity.confidence_score * 100).toFixed(0)}%`}
                            color={getConfidenceColor(opportunity.confidence_score)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            ₹{opportunity.entry_price.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="success.main">
                            ₹{opportunity.target_price.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="error.main">
                            ₹{opportunity.stop_loss.toFixed(2)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={`1:${opportunity.risk_reward_ratio.toFixed(1)}`}
                            color="info"
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {(opportunity.volume / 1000).toFixed(0)}K
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="View Details">
                              <IconButton size="small">
                                <Visibility />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Execute Trade">
                              <IconButton 
                                size="small" 
                                color="success"
                                disabled={opportunity.confidence_score < 0.7}
                              >
                                <CheckCircle />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h6" color="textSecondary" gutterBottom>
                  No Trading Opportunities Found
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  The market scanner is running but no opportunities meet the current criteria.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Strategy Performance Summary */}
      {opportunities.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Strategy Performance Summary
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(
                opportunities.reduce((acc, opp) => {
                  acc[opp.strategy_name] = (acc[opp.strategy_name] || 0) + 1;
                  return acc;
                }, {} as Record<string, number>)
              ).map(([strategy, count]) => (
                <Grid item xs={12} sm={6} md={3} key={strategy}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h6" color="primary">
                      {count}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {strategy}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Universe Configuration Dialog */}
      <Dialog 
        open={universeDialogOpen} 
        onClose={() => setUniverseDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Settings />
            <Typography variant="h6">Configure Stock Universe</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Select a stock universe for market scanning. Different universes provide different 
            coverage and performance characteristics.
          </Typography>

          {/* Current Universe Info */}
          {currentUniverse && (
            <Paper sx={{ p: 2, mb: 3, backgroundColor: 'primary.light', color: 'primary.contrastText' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1 }}>
                Current Universe: {currentUniverse.universe_name}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                Scanning {currentUniverse.stock_count} stocks
              </Typography>
              <Typography variant="caption">
                Sample stocks: {currentUniverse.stocks.join(', ')}
                {currentUniverse.stocks.length < currentUniverse.stock_count && '...'}
              </Typography>
            </Paper>
          )}

          {/* Universe Options */}
          <List>
            {availableUniverses
              .sort((a, b) => a.category.localeCompare(b.category))
              .map((universe) => (
              <ListItem 
                key={universe.id}
                button
                selected={selectedUniverseId === universe.id}
                onClick={() => setSelectedUniverseId(universe.id)}
                sx={{ 
                  border: 1, 
                  borderColor: selectedUniverseId === universe.id ? 'primary.main' : 'divider',
                  borderRadius: 1,
                  mb: 1,
                  backgroundColor: selectedUniverseId === universe.id ? 'primary.light' : 'transparent'
                }}
              >
                <ListItemIcon sx={{ color: getCategoryColor(universe.category) }}>
                  {getCategoryIcon(universe.category)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {universe.name}
                      </Typography>
                      <Chip 
                        label={universe.category.toUpperCase()} 
                        size="small"
                        sx={{ 
                          backgroundColor: getCategoryColor(universe.category),
                          color: 'white',
                          fontSize: '0.7rem'
                        }}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {universe.description}
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                        {universe.stock_count} stocks
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button 
            onClick={() => setUniverseDialogOpen(false)}
            disabled={universeLoading}
          >
            Cancel
          </Button>
          <Button 
            variant="contained"
            onClick={() => updateUniverse(selectedUniverseId)}
            disabled={universeLoading || selectedUniverseId === currentUniverse?.universe_id}
            startIcon={universeLoading ? <CircularProgress size={16} /> : <CheckCircle />}
          >
            {universeLoading ? 'Updating...' : 'Apply Universe'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MarketScanner; 