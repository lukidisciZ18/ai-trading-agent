#!/usr/bin/env python3
"""
AI Trading Agent - Main Entry Point

Production-ready AI trading agent for high-leverage ETF momentum trading
with advanced sentiment analysis, technical indicators, and risk management.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import signal engine modules
try:
    from signals.sentiment import score_sentiment
    from signals.volume import detect_volume_spikes
    from signals.ta_triggers import generate_ta_triggers
    from signals.macro_filter import get_macro_signal
    from signals.sector_rotation import get_sector_rotation_signal
    from signals.etf_premium_discount import get_etf_premium_discount
except ImportError:
    # Handle different import paths
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from signals.sentiment import score_sentiment
    from signals.volume import detect_volume_spikes
    from signals.ta_triggers import generate_ta_triggers
    from signals.macro_filter import get_macro_signal
    from signals.sector_rotation import get_sector_rotation_signal
    from signals.etf_premium_discount import get_etf_premium_discount

class AITradingAgent:
    """
    Main AI Trading Agent class.
    Coordinates data collection, signal generation, and trade execution.
    """
    
    def __init__(self):
        self.symbols = ["TQQQ", "SOXL", "LABU"]  # High-leverage ETF focus
        self.data_path = Path(__file__).parent.parent / "data"
        self.scripts_path = Path(__file__).parent.parent / "scripts"
        self.strategies_path = Path(__file__).parent.parent / "strategies"
        
        # Initialize signal engine components
        print("🧠 Signal Engine: Sentiment + Volume + Technical + Macro + Premium/Discount Analysis")
    
    def collect_market_data(self):
        """Collect live market data from all sources."""
        print("\n🔍 Collecting Market Data...")
        
        # Use your working data collection script
        sys.path.insert(0, str(self.scripts_path))
        
        try:
            from simple_data_collector import collect_all_data
            
            # Collect data for your target symbols
            all_data = collect_all_data(
                symbols=self.symbols,
                reddit_limit=5,
                news_limit=5
            )
            
            if not all_data.empty:
                # Save to data directory
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = self.data_path / f"trading_data_{timestamp}.csv"
                all_data.to_csv(filename, index=False)
                
                # Update latest file
                latest_file = self.data_path / "trading_data_latest.csv"
                all_data.to_csv(latest_file, index=False)
                
                print(f"✅ Collected {len(all_data)} data points")
                print(f"💾 Saved to: {filename}")
                return all_data
            else:
                print("⚠️ No data collected")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Data collection error: {e}")
            return pd.DataFrame()
    
    def generate_trading_signals(self):
        """Generate enhanced trading signals using combined signal engines."""
        print("\n🎯 Generating Trading Signals...")
        
        try:
            # Add strategies directory to path
            sys.path.insert(0, str(self.strategies_path))
            
            from momentum_strategy import TradingSignalGenerator
            
            # Initialize your strategy
            signal_generator = TradingSignalGenerator()
            
            # Generate base signals for your symbols
            signals_df = signal_generator.generate_etf_signals(self.symbols)
            
            if not signals_df.empty:
                # Enhance signals with advanced signal engine
                enhanced_signals = self.enhance_signals_with_engine(signals_df)
                
                # Save enhanced signals
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = self.data_path / f"trading_signals_{timestamp}.csv"
                enhanced_signals.to_csv(filename, index=False)
                
                # Update latest signals
                latest_file = self.data_path / "trading_signals_latest.csv"
                enhanced_signals.to_csv(latest_file, index=False)
                
                print(f"✅ Generated {len(enhanced_signals)} trading signals")
                print(f"💾 Saved to: {filename}")
                
                # Display enhanced signals summary
                self.display_enhanced_signals(enhanced_signals)
                
                return enhanced_signals
            else:
                print("⚠️ No signals generated")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Signal generation error: {e}")
            return pd.DataFrame()
    
    def enhance_signals_with_engine(self, base_signals: pd.DataFrame) -> pd.DataFrame:
        """
        Enhance base trading signals with sentiment, volume, and technical analysis.
        
        Args:
            base_signals: Base signals from momentum strategy
            
        Returns:
            Enhanced signals with combined scores
        """
        enhanced_signals = base_signals.copy()
        
        for idx, signal in enhanced_signals.iterrows():
            symbol = signal['symbol']
            
            try:
                # Get price data for analysis
                price_data = self.get_symbol_data(symbol)
                
                # 1. Technical Analysis Enhancement
                ta_signals = generate_ta_triggers(price_data)
                
                # 2. Volume Analysis Enhancement  
                volume_signals = detect_volume_spikes(price_data)
                
                # 3. Sentiment Analysis (from latest data file)
                sentiment_score = self.get_symbol_sentiment(symbol)
                
                # 4. Simple Macro Filter (VIX + QQQ momentum)
                macro_signal = get_macro_signal()
                
                # 5. ETF Premium/Discount Monitor
                etf_premium_data = get_etf_premium_discount()
                etf_signal = etf_premium_data.get(symbol, {}).get('signal', 0)
                
                # Combine signals into enhanced score
                combined_score = self.calculate_combined_signal_score(
                    base_signal=signal['strength'],
                    ta_signals=ta_signals,
                    volume_signals=volume_signals,
                    sentiment_score=sentiment_score,
                    macro_score=macro_signal['combined_score'],
                    etf_premium_score=etf_signal
                )
                
                # Update enhanced signals
                enhanced_signals.loc[idx, 'enhanced_strength'] = combined_score['combined_strength']
                enhanced_signals.loc[idx, 'sentiment_score'] = combined_score['sentiment']
                enhanced_signals.loc[idx, 'volume_score'] = combined_score['volume']
                enhanced_signals.loc[idx, 'technical_score'] = combined_score['technical']
                enhanced_signals.loc[idx, 'macro_score'] = combined_score['macro']
                enhanced_signals.loc[idx, 'etf_premium_score'] = combined_score['etf_premium']
                enhanced_signals.loc[idx, 'confidence'] = combined_score['confidence']
                
                # Update action based on enhanced strength
                if combined_score['combined_strength'] >= 3:
                    enhanced_signals.loc[idx, 'enhanced_action'] = 'STRONG_BUY'
                elif combined_score['combined_strength'] >= 1:
                    enhanced_signals.loc[idx, 'enhanced_action'] = 'BUY'
                elif combined_score['combined_strength'] <= -3:
                    enhanced_signals.loc[idx, 'enhanced_action'] = 'STRONG_SELL'
                elif combined_score['combined_strength'] <= -1:
                    enhanced_signals.loc[idx, 'enhanced_action'] = 'SELL'
                else:
                    enhanced_signals.loc[idx, 'enhanced_action'] = 'HOLD'
                
            except Exception as e:
                print(f"⚠️ Error enhancing signal for {symbol}: {e}")
                # Keep original signal if enhancement fails
                enhanced_signals.loc[idx, 'enhanced_strength'] = signal['strength']
                enhanced_signals.loc[idx, 'enhanced_action'] = signal.get('action', 'HOLD')
                enhanced_signals.loc[idx, 'sentiment_score'] = 0
                enhanced_signals.loc[idx, 'volume_score'] = 0
                enhanced_signals.loc[idx, 'technical_score'] = 0
                enhanced_signals.loc[idx, 'macro_score'] = 0
                enhanced_signals.loc[idx, 'etf_premium_score'] = 0
                enhanced_signals.loc[idx, 'confidence'] = 0.5
        
        return enhanced_signals
    
    def calculate_combined_signal_score(self, base_signal: int, ta_signals: pd.DataFrame, 
                                      volume_signals: pd.DataFrame, sentiment_score: float, 
                                      macro_score: float = 0.0, etf_premium_score: float = 0.0) -> Dict:
        """
        Combine all signal sources into weighted composite score.
        
        Returns:
            Dict with combined scores and confidence metrics
        """
        # Simple weights for signal combination
        weights = {
            'base': 0.30,        # 30% - Your proven momentum strategy
            'technical': 0.25,   # 25% - Technical analysis triggers
            'volume': 0.20,      # 20% - Volume confirmation
            'sentiment': 0.10,   # 10% - Sentiment bias
            'macro': 0.10,       # 10% - Simple macro filter (VIX + momentum)
            'etf_premium': 0.05  #  5% - ETF premium/discount timing
        }
        
        # Extract scores from each engine
        technical_score = 0
        if not ta_signals.empty and len(ta_signals) > 0:
            # Sum signal strengths from technical analysis
            if 'signal_strength' in ta_signals.columns:
                technical_score = ta_signals['signal_strength'].sum()
            elif 'strength' in ta_signals.columns:
                technical_score = ta_signals['strength'].sum()
            else:
                # Default based on number of signals
                technical_score = len(ta_signals) * (1 if base_signal > 0 else -1)
        
        volume_score = 0
        if not volume_signals.empty and len(volume_signals) > 0:
            # Extract volume signal strength
            if 'volume_signal_strength' in volume_signals.columns:
                volume_score = volume_signals['volume_signal_strength'].iloc[0]
            elif 'signal_strength' in volume_signals.columns:
                volume_score = volume_signals['signal_strength'].iloc[0]
            elif 'volume_spike_strength' in volume_signals.columns:
                volume_score = volume_signals['volume_spike_strength'].iloc[0]
            else:
                # Use volume ratio as proxy
                volume_score = volume_signals.get('volume_ratio', pd.Series([1.0])).iloc[0] - 1.0
        
        # Calculate weighted combined strength
        combined_strength = (
            weights['base'] * base_signal +
            weights['technical'] * technical_score +
            weights['volume'] * volume_score +
            weights['sentiment'] * sentiment_score +
            weights['macro'] * macro_score +
            weights['etf_premium'] * etf_premium_score
        )
        
        # Calculate confidence based on signal alignment
        signal_alignment = abs(base_signal) + abs(technical_score) + abs(volume_score) + abs(macro_score) + abs(etf_premium_score)
        confidence = min(signal_alignment / 15.0, 1.0)  # Max confidence = 1.0
        
        return {
            'combined_strength': round(combined_strength, 2),
            'sentiment': sentiment_score,
            'volume': volume_score,
            'technical': technical_score,
            'macro': macro_score,
            'etf_premium': etf_premium_score,
            'confidence': round(confidence, 3)
        }
    
    def get_symbol_sentiment(self, symbol: str) -> float:
        """
        Get sentiment score for a symbol from latest collected data using VADER.
        
        Returns:
            Sentiment score between -1 (bearish) and +1 (bullish)
        """
        try:
            # Load latest data file
            latest_file = self.data_path / "trading_data_latest.csv"
            if latest_file.exists():
                data = pd.read_csv(latest_file)
                
                # Filter data for the symbol
                symbol_data = data[data['symbol'] == symbol]
                
                if not symbol_data.empty and 'text' in symbol_data.columns:
                    # Use your VADER sentiment analysis
                    sentiment_df = score_sentiment(symbol_data)
                    
                    # Return average sentiment for this symbol
                    return sentiment_df['sentiment'].mean()
            
            return 0.0  # Neutral if no data
            
        except Exception as e:
            print(f"⚠️ Error getting sentiment for {symbol}: {e}")
            return 0.0
    
    def get_symbol_data(self, symbol: str) -> pd.DataFrame:
        """
        Get price and volume data for a symbol.
        
        Returns:
            DataFrame with OHLCV data for the symbol
        """
        try:
            # Try to get data from latest collected data first
            latest_file = self.data_path / "trading_data_latest.csv"
            if latest_file.exists():
                data = pd.read_csv(latest_file)
                symbol_data = data[data['symbol'] == symbol]
                
                # Check if we have the required columns
                required_cols = ['open', 'high', 'low', 'close', 'volume']
                if not symbol_data.empty and all(col in symbol_data.columns for col in required_cols):
                    return symbol_data
            
            # Fallback: Get fresh data using yfinance
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="60d")
            
            if not data.empty:
                # Reset index to get date as column
                data = data.reset_index()
                data['symbol'] = symbol
                data['timestamp'] = data['Date'] if 'Date' in data.columns else pd.date_range('2025-01-01', periods=len(data))
                
                # Rename columns to match expected format
                data = data.rename(columns={
                    'Open': 'open',
                    'High': 'high', 
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                
                return data[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # If all else fails, return empty DataFrame
            return pd.DataFrame()
            
        except Exception as e:
            print(f"⚠️ Error getting data for {symbol}: {e}")
            return pd.DataFrame()
    
    def display_enhanced_signals(self, signals: pd.DataFrame):
        """Display enhanced signals summary."""
        if signals.empty:
            return
        
        print("\n📈 Enhanced Trading Opportunities:")
        
        # Sort by enhanced strength (strongest signals first)
        if 'enhanced_strength' in signals.columns:
            sorted_signals = signals.sort_values('enhanced_strength', ascending=False)
        else:
            sorted_signals = signals.sort_values('strength', ascending=False)
        
        for _, signal in sorted_signals.head(5).iterrows():  # Top 5 signals
            symbol = signal['symbol']
            action = signal.get('enhanced_action', signal.get('action', signal.get('signal', 'UNKNOWN')))
            price = signal.get('price', signal.get('entry_price', 'N/A'))
            confidence = signal.get('confidence', 0)
            sentiment = signal.get('sentiment_score', 0)
            enhanced_strength = signal.get('enhanced_strength', signal.get('strength', 0))
            
            print(f"   {symbol}: {action} at ${price}")
            print(f"      Confidence: {confidence:.1%}")
            print(f"      Sentiment: {sentiment:+.2f}")
            print(f"      Enhanced Strength: {enhanced_strength:+.1f}")
            print()
    def run_full_cycle(self):
        """Run complete AI trading cycle: data collection + enhanced signal generation."""
        print("🚀 RUNNING FULL AI TRADING CYCLE")
        print("=" * 50)
        
        # Step 1: Collect market data
        market_data = self.collect_market_data()
        
        # Step 2: Generate enhanced trading signals
        trading_signals = self.generate_trading_signals()
        
        # Summary
        print(f"\n📊 CYCLE COMPLETE")
        print("-" * 20)
        print(f"Data Points: {len(market_data) if not market_data.empty else 0}")
        print(f"Trading Signals: {len(trading_signals) if not trading_signals.empty else 0}")
        
        if not trading_signals.empty:
            print(f"\n🔥 AI Trading Agent with Enhanced Signal Engine Ready!")
            return True
        else:
            print(f"\n⚠️ No actionable signals - check market conditions")
            return False
    
    def test_integration(self):
        """Test all systems are working properly."""
        print("🧪 TESTING AI TRADING AGENT INTEGRATION")
        print("=" * 50)
        
        # Test data collection
        print("1. Testing Data Collection...")
        try:
            sys.path.insert(0, str(self.scripts_path))
            
            # Run your integration test
            import subprocess
            result = subprocess.run([
                "python", 
                str(self.scripts_path / "final_integration_test.py")
            ], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
            
            if result.returncode == 0:
                print("   ✅ Data collection working")
            else:
                print("   ⚠️ Data collection issues detected")
                print(f"   Error: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Integration test error: {e}")
        
        # Test signal generation
        print("\n2. Testing Signal Generation...")
        try:
            signals_df = self.generate_trading_signals()
            if not signals_df.empty:
                print("   ✅ Signal generation working")
            else:
                print("   ⚠️ No signals generated")
        except Exception as e:
            print(f"   ❌ Signal generation error: {e}")
        
        print(f"\n🎯 Integration test complete!")

def main():
    """Main function - entry point for AI Trading Agent."""
    
    # Initialize the AI agent
    agent = AITradingAgent()
    
    # Command line interface
    import argparse
    parser = argparse.ArgumentParser(description='AI Trading Agent')
    parser.add_argument('--mode', choices=['run', 'test', 'collect', 'signals'], 
                       default='run', help='Operation mode')
    
    args = parser.parse_args()
    
    if args.mode == 'test':
        agent.test_integration()
    elif args.mode == 'collect':
        agent.collect_market_data()
    elif args.mode == 'signals':
        agent.generate_trading_signals()
    else:  # run
        agent.run_full_cycle()

if __name__ == "__main__":
    main()
