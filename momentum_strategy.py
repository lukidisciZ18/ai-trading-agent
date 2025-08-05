#!/usr/bin/env python3
"""
AI Trading Agent - High-Leverage ETF & Small-Cap Momentum Strategy

Focus: Technical patterns on TQQQ, SOXL, LABU + AI sentiment on small-caps
Risk: -8% SL, +20% TP (50% sell), trail to breakeven
"""

import os
import yfinance as yf
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import praw

load_dotenv()

class TradingSignalGenerator:
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.reddit = self._init_reddit()
        
        # Your strategy parameters
        self.stop_loss_pct = -8.0
        self.take_profit_pct = 20.0
        self.partial_sell_pct = 50.0  # Sell 50% at TP1
        
        # Target universes
        self.leverage_etfs = ["TQQQ", "SOXL", "LABU", "TECL", "FNGU", "BULZ", "WEBL"]
        self.small_caps = []  # Will be populated with small-cap discoveries
        
    def _init_reddit(self):
        """Initialize Reddit client"""
        try:
            return praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent=os.getenv("REDDIT_USER_AGENT"),
            )
        except:
            return None

    def get_technical_analysis(self, symbol: str, period: str = "60d") -> Dict:
        """
        Get technical analysis for a symbol with your specific indicators:
        RSI(14), MACD(12,26,9), Volume MA(20)
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if len(hist) < 26:  # Need minimum data
                return {}
            
            # Convert to numpy arrays and ensure float64
            close = hist['Close'].values.astype(np.float64)
            volume = hist['Volume'].values.astype(np.float64)
            high = hist['High'].values.astype(np.float64)
            low = hist['Low'].values.astype(np.float64)
            
            import talib
            
            # RSI (14 period)
            rsi = talib.RSI(close, timeperiod=14)
            current_rsi = rsi[-1] if not np.isnan(rsi[-1]) else None
            
            # MACD (12,26,9)
            macd, macdsignal, macdhist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            current_macd = macd[-1] if not np.isnan(macd[-1]) else None
            current_macd_signal = macdsignal[-1] if not np.isnan(macdsignal[-1]) else None
            current_macd_hist = macdhist[-1] if not np.isnan(macdhist[-1]) else None
            
            # Volume MA (20 period)
            volume_ma = talib.SMA(volume, timeperiod=20)
            current_volume_ma = volume_ma[-1] if not np.isnan(volume_ma[-1]) else None
            current_volume = volume[-1]
            volume_surge = (current_volume / current_volume_ma) if current_volume_ma else None
            
            # Price metrics
            current_price = close[-1]
            price_5d_ago = close[-5] if len(close) >= 5 else close[0]
            price_20d_ago = close[-20] if len(close) >= 20 else close[0]
            
            momentum_5d = ((current_price - price_5d_ago) / price_5d_ago * 100) if price_5d_ago else None
            momentum_20d = ((current_price - price_20d_ago) / price_20d_ago * 100) if price_20d_ago else None
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20)
            bb_position = ((current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])) if not np.isnan(bb_upper[-1]) else None
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'rsi_14': current_rsi,
                'macd': current_macd,
                'macd_signal': current_macd_signal,
                'macd_histogram': current_macd_hist,
                'volume_surge_ratio': volume_surge,
                'momentum_5d': momentum_5d,
                'momentum_20d': momentum_20d,
                'bb_position': bb_position,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"Technical analysis error for {symbol}: {e}")
            return {}

    def generate_etf_signals(self, symbols: List[str]) -> pd.DataFrame:
        """
        Generate trading signals for high-leverage ETFs based on technical patterns
        """
        signals = []
        
        for symbol in symbols:
            try:
                tech_data = self.get_technical_analysis(symbol)
                
                if not tech_data:
                    continue
                
                # Signal generation logic for your strategy
                signal_strength = 0
                signal_type = "HOLD"
                reasons = []
                
                rsi = tech_data.get('rsi_14')
                macd_hist = tech_data.get('macd_histogram')
                volume_surge = tech_data.get('volume_surge_ratio')
                momentum_5d = tech_data.get('momentum_5d')
                bb_position = tech_data.get('bb_position')
                
                # BUY signals (momentum entry)
                if rsi and rsi < 30:  # Oversold RSI
                    signal_strength += 2
                    reasons.append("RSI oversold")
                
                if macd_hist and macd_hist > 0:  # MACD turning positive
                    signal_strength += 2
                    reasons.append("MACD bullish")
                
                if volume_surge and volume_surge > 1.5:  # High volume
                    signal_strength += 1
                    reasons.append("Volume surge")
                
                if momentum_5d and momentum_5d > 5:  # Strong 5-day momentum
                    signal_strength += 2
                    reasons.append("Strong momentum")
                
                if bb_position and bb_position < 0.2:  # Near lower Bollinger Band
                    signal_strength += 1
                    reasons.append("Near BB support")
                
                # SELL signals (momentum exit)
                if rsi and rsi > 70:  # Overbought RSI
                    signal_strength -= 2
                    reasons.append("RSI overbought")
                
                if macd_hist and macd_hist < 0:  # MACD turning negative
                    signal_strength -= 2
                    reasons.append("MACD bearish")
                
                if momentum_5d and momentum_5d < -5:  # Negative momentum
                    signal_strength -= 2
                    reasons.append("Weak momentum")
                
                # Determine signal
                if signal_strength >= 4:
                    signal_type = "STRONG_BUY"
                elif signal_strength >= 2:
                    signal_type = "BUY"
                elif signal_strength <= -4:
                    signal_type = "STRONG_SELL"
                elif signal_strength <= -2:
                    signal_type = "SELL"
                
                # Calculate position sizing and risk management
                entry_price = tech_data['current_price']
                stop_loss_price = entry_price * (1 + self.stop_loss_pct / 100)
                take_profit_price = entry_price * (1 + self.take_profit_pct / 100)
                
                signals.append({
                    'symbol': symbol,
                    'signal': signal_type,
                    'strength': signal_strength,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price,
                    'reasons': ', '.join(reasons),
                    'rsi': rsi,
                    'macd_hist': macd_hist,
                    'volume_surge': volume_surge,
                    'momentum_5d': momentum_5d,
                    'timestamp': datetime.now()
                })
                
                print(f"📊 {symbol}: {signal_type} (strength: {signal_strength}) - {', '.join(reasons)}")
                
            except Exception as e:
                print(f"Error generating signal for {symbol}: {e}")
                continue
        
        return pd.DataFrame(signals)

    def get_reddit_sentiment(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get Reddit sentiment for symbols from financial subreddits
        """
        if not self.reddit:
            return {}
        
        sentiment_scores = {}
        
        try:
            subreddits = ['stocks', 'investing', 'SecurityAnalysis', 'pennystocks', 'smallstreetbets']
            
            for symbol in symbols:
                positive_mentions = 0
                total_mentions = 0
                
                for subreddit in subreddits:
                    try:
                        query = f"${symbol}"
                        posts = list(self.reddit.subreddit(subreddit).search(query, limit=10, time_filter='week'))
                        
                        for post in posts:
                            total_mentions += 1
                            title_text = f"{post.title} {post.selftext}".lower()
                            
                            # Simple sentiment scoring
                            positive_words = ['buy', 'bullish', 'moon', 'rocket', 'calls', 'long', 'pump', 'green', 'up', 'gain']
                            negative_words = ['sell', 'bearish', 'puts', 'short', 'dump', 'red', 'down', 'loss', 'crash']
                            
                            pos_count = sum(1 for word in positive_words if word in title_text)
                            neg_count = sum(1 for word in negative_words if word in title_text)
                            
                            if pos_count > neg_count:
                                positive_mentions += 1
                    
                    except Exception as e:
                        continue
                
                if total_mentions > 0:
                    sentiment_scores[symbol] = positive_mentions / total_mentions
                else:
                    sentiment_scores[symbol] = 0.5  # Neutral
                    
        except Exception as e:
            print(f"Reddit sentiment error: {e}")
        
        return sentiment_scores

    def run_strategy_scan(self) -> pd.DataFrame:
        """
        Run complete strategy scan: ETF technical analysis + small-cap sentiment
        """
        print("🚀 Running AI Trading Strategy Scan")
        print("=" * 50)
        
        # 1. High-Leverage ETF Technical Analysis
        print("📊 Analyzing High-Leverage ETFs for Technical Patterns...")
        etf_signals = self.generate_etf_signals(self.leverage_etfs)
        
        # 2. Get Reddit sentiment for ETFs
        print("📱 Getting Reddit Sentiment...")
        sentiment_scores = self.get_reddit_sentiment(self.leverage_etfs)
        
        # 3. Combine signals with sentiment
        if not etf_signals.empty:
            etf_signals['reddit_sentiment'] = etf_signals['symbol'].map(sentiment_scores)
            
            # Boost signals with positive sentiment
            etf_signals['final_score'] = etf_signals['strength'] + (etf_signals['reddit_sentiment'] - 0.5) * 2
            
        # 4. Export results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"trading_signals_{timestamp}.csv"
        etf_signals.to_csv(filename, index=False)
        
        print(f"\n💾 Trading signals exported: {filename}")
        
        # 5. Display top opportunities
        if not etf_signals.empty:
            print(f"\n🎯 Top Trading Opportunities:")
            top_signals = etf_signals.nlargest(3, 'final_score')
            
            for _, signal in top_signals.iterrows():
                print(f"\n📈 {signal['symbol']} - {signal['signal']}")
                print(f"   Entry: ${signal['entry_price']:.2f}")
                print(f"   Stop Loss: ${signal['stop_loss']:.2f} ({self.stop_loss_pct}%)")
                print(f"   Take Profit: ${signal['take_profit']:.2f} ({self.take_profit_pct}%)")
                print(f"   Reasons: {signal['reasons']}")
                print(f"   Sentiment: {signal['reddit_sentiment']:.1%}")
        
        return etf_signals

# Example usage
if __name__ == "__main__":
    # Initialize your trading strategy
    strategy = TradingSignalGenerator()
    
    # Run the complete analysis
    signals = strategy.run_strategy_scan()
    
    print(f"\n🔥 AI Trading Agent Strategy Complete!")
    print(f"📊 Found {len(signals)} opportunities")
    print(f"🎯 Risk Management: {strategy.stop_loss_pct}% SL, {strategy.take_profit_pct}% TP")
    print(f"💰 Focus: High-leverage ETFs with technical momentum patterns")
