"""
EOD (End of Day) Summary Generator
Generates comprehensive daily reports of market scanning results and performance metrics.
"""

import json
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import seaborn as sns

from ..core.logging_service import LoggingService
from ..core.config import ConfigurationManager
from .market_scanner import MarketScanResult, TradingOpportunity


@dataclass
class DailyOpportunitySummary:
    """Summary of opportunities found in a day."""
    date: str
    total_stocks_scanned: int
    opportunities_found: int
    buy_signals: int
    sell_signals: int
    short_signals: int
    avg_confidence_score: float
    avg_risk_reward_ratio: float
    top_opportunities: List[Dict[str, Any]]
    sector_breakdown: Dict[str, int]
    strategy_performance: Dict[str, int]


@dataclass
class EODReport:
    """Complete EOD report."""
    report_date: str
    market_sentiment: str
    scan_summary: DailyOpportunitySummary
    missed_opportunities: List[Dict[str, Any]]
    strategy_analysis: Dict[str, Any]
    market_analysis: Dict[str, Any]
    recommendations: List[str]
    risk_metrics: Dict[str, Any]
    generated_at: str


class EODSummaryGenerator:
    """
    EOD Summary Generator
    Creates comprehensive daily reports of market scanning and trading opportunities.
    """
    
    def __init__(self, config: ConfigurationManager):
        """Initialize the EOD summary generator."""
        self.config = config
        self.logger = LoggingService()
        
        # Report storage
        self.daily_reports: List[EODReport] = []
        self.opportunity_history: List[TradingOpportunity] = []
        
        # Configuration
        self.report_retention_days = getattr(config.eod_summary, 'report_retention_days', 30)
        self.min_confidence_threshold = getattr(config.eod_summary, 'min_confidence_threshold', 0.7)
        
        self.logger.info("EOD Summary Generator initialized")
    
    def add_scan_result(self, scan_result: MarketScanResult):
        """Add a scan result to the daily tracking."""
        try:
            # Store opportunities in history
            self.opportunity_history.extend(scan_result.opportunities)
            
            # Clean old data
            self._cleanup_old_data()
            
            self.logger.debug(f"Added scan result with {len(scan_result.opportunities)} opportunities")
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "add_scan_result"})
    
    def generate_daily_report(self, date: str = None) -> EODReport:
        """Generate comprehensive EOD report for a specific date."""
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Get opportunities for the specified date
            daily_opportunities = self._get_daily_opportunities(date)
            
            if not daily_opportunities:
                self.logger.warning(f"No opportunities found for date: {date}")
                return self._generate_empty_report(date)
            
            # Generate summary components
            opportunity_summary = self._generate_opportunity_summary(daily_opportunities, date)
            missed_opportunities = self._identify_missed_opportunities(daily_opportunities)
            strategy_analysis = self._analyze_strategy_performance(daily_opportunities)
            market_analysis = self._analyze_market_conditions(daily_opportunities)
            recommendations = self._generate_recommendations(daily_opportunities, strategy_analysis)
            risk_metrics = self._calculate_risk_metrics(daily_opportunities)
            
            # Create EOD report
            eod_report = EODReport(
                report_date=date,
                market_sentiment=self._determine_market_sentiment(daily_opportunities),
                scan_summary=opportunity_summary,
                missed_opportunities=missed_opportunities,
                strategy_analysis=strategy_analysis,
                market_analysis=market_analysis,
                recommendations=recommendations,
                risk_metrics=risk_metrics,
                generated_at=datetime.now().isoformat()
            )
            
            # Store report
            self.daily_reports.append(eod_report)
            
            self.logger.info(f"Generated EOD report for {date} with {len(daily_opportunities)} opportunities")
            return eod_report
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_daily_report", "date": date})
            return self._generate_empty_report(date)
    
    def _get_daily_opportunities(self, date: str) -> List[TradingOpportunity]:
        """Get all opportunities for a specific date."""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            daily_opportunities = []
            for opportunity in self.opportunity_history:
                if opportunity.timestamp.date() == target_date:
                    daily_opportunities.append(opportunity)
            
            return daily_opportunities
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_daily_opportunities", "date": date})
            return []
    
    def _generate_opportunity_summary(self, opportunities: List[TradingOpportunity], date: str) -> DailyOpportunitySummary:
        """Generate summary of daily opportunities."""
        try:
            if not opportunities:
                return DailyOpportunitySummary(
                    date=date,
                    total_stocks_scanned=0,
                    opportunities_found=0,
                    buy_signals=0,
                    sell_signals=0,
                    short_signals=0,
                    avg_confidence_score=0.0,
                    avg_risk_reward_ratio=0.0,
                    top_opportunities=[],
                    sector_breakdown={},
                    strategy_performance={}
                )
            
            # Count signal types
            buy_signals = sum(1 for opp in opportunities if opp.signal_type == "BUY")
            sell_signals = sum(1 for opp in opportunities if opp.signal_type == "SELL")
            short_signals = sum(1 for opp in opportunities if opp.signal_type == "SHORT")
            
            # Calculate averages
            avg_confidence = sum(opp.confidence_score for opp in opportunities) / len(opportunities)
            avg_risk_reward = sum(opp.risk_reward_ratio for opp in opportunities) / len(opportunities)
            
            # Get top opportunities (highest confidence)
            top_opportunities = sorted(opportunities, key=lambda x: x.confidence_score, reverse=True)[:10]
            top_opps_data = [
                {
                    "symbol": opp.symbol,
                    "strategy": opp.strategy_name,
                    "signal": opp.signal_type,
                    "confidence": opp.confidence_score,
                    "risk_reward": opp.risk_reward_ratio,
                    "description": opp.description
                }
                for opp in top_opportunities
            ]
            
            # Sector breakdown (simplified - using symbol prefixes)
            sector_breakdown = {}
            for opp in opportunities:
                sector = self._get_sector_from_symbol(opp.symbol)
                sector_breakdown[sector] = sector_breakdown.get(sector, 0) + 1
            
            # Strategy performance
            strategy_performance = {}
            for opp in opportunities:
                strategy = opp.strategy_name
                strategy_performance[strategy] = strategy_performance.get(strategy, 0) + 1
            
            return DailyOpportunitySummary(
                date=date,
                total_stocks_scanned=len(set(opp.symbol for opp in opportunities)),  # Approximate
                opportunities_found=len(opportunities),
                buy_signals=buy_signals,
                sell_signals=sell_signals,
                short_signals=short_signals,
                avg_confidence_score=round(avg_confidence, 3),
                avg_risk_reward_ratio=round(avg_risk_reward, 2),
                top_opportunities=top_opps_data,
                sector_breakdown=sector_breakdown,
                strategy_performance=strategy_performance
            )
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_opportunity_summary"})
            return DailyOpportunitySummary(
                date=date,
                total_stocks_scanned=0,
                opportunities_found=0,
                buy_signals=0,
                sell_signals=0,
                short_signals=0,
                avg_confidence_score=0.0,
                avg_risk_reward_ratio=0.0,
                top_opportunities=[],
                sector_breakdown={},
                strategy_performance={}
            )
    
    def _identify_missed_opportunities(self, opportunities: List[TradingOpportunity]) -> List[Dict[str, Any]]:
        """Identify potentially missed opportunities."""
        try:
            missed_opportunities = []
            
            # Find opportunities with high confidence but not executed
            high_confidence_opps = [
                opp for opp in opportunities 
                if opp.confidence_score >= 0.8 and opp.confidence_score < self.min_confidence_threshold
            ]
            
            for opp in high_confidence_opps:
                missed_opp = {
                    "symbol": opp.symbol,
                    "strategy": opp.strategy_name,
                    "signal": opp.signal_type,
                    "confidence": opp.confidence_score,
                    "reason": "Below confidence threshold",
                    "potential_loss": "High confidence opportunity not captured"
                }
                missed_opportunities.append(missed_opp)
            
            return missed_opportunities
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "identify_missed_opportunities"})
            return []
    
    def _analyze_strategy_performance(self, opportunities: List[TradingOpportunity]) -> Dict[str, Any]:
        """Analyze performance of different strategies."""
        try:
            strategy_stats = {}
            
            for opp in opportunities:
                strategy = opp.strategy_name
                
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        "total_signals": 0,
                        "buy_signals": 0,
                        "sell_signals": 0,
                        "short_signals": 0,
                        "avg_confidence": 0.0,
                        "avg_risk_reward": 0.0,
                        "total_confidence": 0.0,
                        "total_risk_reward": 0.0
                    }
                
                stats = strategy_stats[strategy]
                stats["total_signals"] += 1
                stats["total_confidence"] += opp.confidence_score
                stats["total_risk_reward"] += opp.risk_reward_ratio
                
                if opp.signal_type == "BUY":
                    stats["buy_signals"] += 1
                elif opp.signal_type == "SELL":
                    stats["sell_signals"] += 1
                elif opp.signal_type == "SHORT":
                    stats["short_signals"] += 1
            
            # Calculate averages
            for strategy, stats in strategy_stats.items():
                if stats["total_signals"] > 0:
                    stats["avg_confidence"] = round(stats["total_confidence"] / stats["total_signals"], 3)
                    stats["avg_risk_reward"] = round(stats["total_risk_reward"] / stats["total_signals"], 2)
            
            return strategy_stats
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "analyze_strategy_performance"})
            return {}
    
    def _analyze_market_conditions(self, opportunities: List[TradingOpportunity]) -> Dict[str, Any]:
        """Analyze overall market conditions."""
        try:
            if not opportunities:
                return {"market_condition": "NO_DATA", "volatility": "UNKNOWN"}
            
            # Analyze signal distribution
            total_signals = len(opportunities)
            buy_ratio = sum(1 for opp in opportunities if opp.signal_type == "BUY") / total_signals
            sell_ratio = sum(1 for opp in opportunities if opp.signal_type in ["SELL", "SHORT"]) / total_signals
            
            # Determine market condition
            if buy_ratio > 0.6:
                market_condition = "BULLISH"
            elif sell_ratio > 0.6:
                market_condition = "BEARISH"
            else:
                market_condition = "NEUTRAL"
            
            # Analyze confidence distribution
            confidence_scores = [opp.confidence_score for opp in opportunities]
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            if avg_confidence > 0.8:
                volatility = "LOW"
            elif avg_confidence > 0.6:
                volatility = "MEDIUM"
            else:
                volatility = "HIGH"
            
            return {
                "market_condition": market_condition,
                "volatility": volatility,
                "buy_ratio": round(buy_ratio, 3),
                "sell_ratio": round(sell_ratio, 3),
                "avg_confidence": round(avg_confidence, 3),
                "total_signals": total_signals
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "analyze_market_conditions"})
            return {"market_condition": "ERROR", "volatility": "UNKNOWN"}
    
    def _generate_recommendations(self, opportunities: List[TradingOpportunity], strategy_analysis: Dict[str, Any]) -> List[str]:
        """Generate trading recommendations based on analysis."""
        try:
            recommendations = []
            
            if not opportunities:
                recommendations.append("No trading opportunities detected today. Consider reducing position sizes.")
                return recommendations
            
            # Strategy-specific recommendations
            for strategy, stats in strategy_analysis.items():
                if stats["total_signals"] > 5:  # High activity strategy
                    if stats["avg_confidence"] > 0.8:
                        recommendations.append(f"Strategy '{strategy}' showing high confidence signals. Consider increasing allocation.")
                    elif stats["avg_confidence"] < 0.6:
                        recommendations.append(f"Strategy '{strategy}' showing low confidence. Consider reducing exposure or reviewing parameters.")
            
            # Market condition recommendations
            market_analysis = self._analyze_market_conditions(opportunities)
            if market_analysis["market_condition"] == "BULLISH":
                recommendations.append("Market showing bullish bias. Focus on long opportunities and momentum strategies.")
            elif market_analysis["market_condition"] == "BEARISH":
                recommendations.append("Market showing bearish bias. Consider defensive positions and mean reversion strategies.")
            
            # Risk management recommendations
            if market_analysis["volatility"] == "HIGH":
                recommendations.append("High market volatility detected. Tighten stop losses and reduce position sizes.")
            
            # Add general recommendations
            recommendations.append("Always maintain proper risk management and position sizing.")
            recommendations.append("Monitor market conditions and adjust strategy parameters as needed.")
            
            return recommendations
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_recommendations"})
            return ["Error generating recommendations. Please check system logs."]
    
    def _calculate_risk_metrics(self, opportunities: List[TradingOpportunity]) -> Dict[str, Any]:
        """Calculate risk metrics for the day."""
        try:
            if not opportunities:
                return {
                    "total_risk": 0.0,
                    "avg_risk_per_opportunity": 0.0,
                    "max_risk_opportunity": None,
                    "risk_distribution": {}
                }
            
            # Calculate risk metrics
            total_risk = sum(opp.risk_reward_ratio for opp in opportunities)
            avg_risk = total_risk / len(opportunities)
            
            # Find highest risk opportunity
            max_risk_opp = max(opportunities, key=lambda x: x.risk_reward_ratio)
            max_risk_info = {
                "symbol": max_risk_opp.symbol,
                "strategy": max_risk_opp.strategy_name,
                "risk_reward": max_risk_opp.risk_reward_ratio,
                "confidence": max_risk_opp.confidence_score
            }
            
            # Risk distribution by strategy
            risk_distribution = {}
            for opp in opportunities:
                strategy = opp.strategy_name
                if strategy not in risk_distribution:
                    risk_distribution[strategy] = []
                risk_distribution[strategy].append(opp.risk_reward_ratio)
            
            # Calculate average risk per strategy
            for strategy, risks in risk_distribution.items():
                risk_distribution[strategy] = round(sum(risks) / len(risks), 2)
            
            return {
                "total_risk": round(total_risk, 2),
                "avg_risk_per_opportunity": round(avg_risk, 2),
                "max_risk_opportunity": max_risk_info,
                "risk_distribution": risk_distribution
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "calculate_risk_metrics"})
            return {"total_risk": 0.0, "avg_risk_per_opportunity": 0.0, "max_risk_opportunity": None, "risk_distribution": {}}
    
    def _determine_market_sentiment(self, opportunities: List[TradingOpportunity]) -> str:
        """Determine overall market sentiment."""
        try:
            if not opportunities:
                return "NEUTRAL"
            
            buy_signals = sum(1 for opp in opportunities if opp.signal_type == "BUY")
            sell_signals = sum(1 for opp in opportunities if opp.signal_type in ["SELL", "SHORT"])
            
            total_signals = len(opportunities)
            buy_ratio = buy_signals / total_signals
            
            if buy_ratio > 0.6:
                return "BULLISH"
            elif buy_ratio < 0.4:
                return "BEARISH"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            self.logger.log_error(e, {"operation": "determine_market_sentiment"})
            return "UNKNOWN"
    
    def _get_sector_from_symbol(self, symbol: str) -> str:
        """Get sector from symbol (simplified mapping)."""
        try:
            # Simplified sector mapping
            sector_mapping = {
                "RELIANCE": "OIL_GAS",
                "TCS": "IT",
                "HDFC": "BANKING",
                "INFY": "IT",
                "ICICIBANK": "BANKING",
                "NIFTY": "INDEX",
                "BANKNIFTY": "INDEX"
            }
            
            return sector_mapping.get(symbol, "OTHERS")
            
        except Exception:
            return "OTHERS"
    
    def _generate_empty_report(self, date: str) -> EODReport:
        """Generate an empty report when no data is available."""
        return EODReport(
            report_date=date,
            market_sentiment="NO_DATA",
            scan_summary=DailyOpportunitySummary(
                date=date,
                total_stocks_scanned=0,
                opportunities_found=0,
                buy_signals=0,
                sell_signals=0,
                short_signals=0,
                avg_confidence_score=0.0,
                avg_risk_reward_ratio=0.0,
                top_opportunities=[],
                sector_breakdown={},
                strategy_performance={}
            ),
            missed_opportunities=[],
            strategy_analysis={},
            market_analysis={"market_condition": "NO_DATA", "volatility": "UNKNOWN"},
            recommendations=["No trading opportunities detected today."],
            risk_metrics={"total_risk": 0.0, "avg_risk_per_opportunity": 0.0},
            generated_at=datetime.now().isoformat()
        )
    
    def _cleanup_old_data(self):
        """Clean up old data based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.report_retention_days)
            
            # Clean up old opportunities
            self.opportunity_history = [
                opp for opp in self.opportunity_history
                if opp.timestamp > cutoff_date
            ]
            
            # Clean up old reports
            self.daily_reports = [
                report for report in self.daily_reports
                if datetime.strptime(report.report_date, "%Y-%m-%d").date() > cutoff_date.date()
            ]
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "cleanup_old_data"})
    
    def export_report_to_json(self, report: EODReport, filepath: str = None) -> str:
        """Export EOD report to JSON format."""
        try:
            if filepath is None:
                filepath = f"eod_report_{report.report_date}.json"
            
            # Convert report to dictionary
            report_dict = asdict(report)
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            self.logger.info(f"EOD report exported to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "export_report_to_json"})
            return ""
    
    def get_report_summary(self, date: str = None) -> Dict[str, Any]:
        """Get a summary of the latest report."""
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Find the report for the specified date
            for report in reversed(self.daily_reports):
                if report.report_date == date:
                    return {
                        "date": report.report_date,
                        "market_sentiment": report.market_sentiment,
                        "opportunities_found": report.scan_summary.opportunities_found,
                        "avg_confidence": report.scan_summary.avg_confidence_score,
                        "top_opportunity": report.scan_summary.top_opportunities[0] if report.scan_summary.top_opportunities else None,
                        "recommendations_count": len(report.recommendations)
                    }
            
            return {"error": f"No report found for date: {date}"}
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "get_report_summary"})
            return {"error": "Failed to get report summary"} 