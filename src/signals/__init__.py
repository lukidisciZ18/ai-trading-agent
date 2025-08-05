#!/usr/bin/env python3
"""
Signal Engine Integration - Master Controller

Integrates sentiment, volume, and technical analysis signals into unified
trading decisions for your AI trading agent.
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class SignalEngine:
    """
    Master signal engine that combines all three signal modules.
    Designed to work seamlessly with your existing trading strategy.
    """
    
    def __init__(self):
        self.signal_weights = {
            'technical_analysis': 0.50,  # Technical signals most important for ETF momentum
            'volume_analysis': 0.30,     # Volume confirms momentum
            'sentiment_analysis': 0.20   # Sentiment provides additional edge
        }
        
        # Risk management integration (your exact parameters)
        self.risk_params = {
            'stop_loss_pct': -8.0,
            'take_profit_pct': 20.0,
            'partial_sell_pct': 50.0
        }
    
    def process_all_signals(self, input_df: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
        """
        Process all signals from sentiment, volume, and technical analysis.
        
        Args:
            input_df: Your combined DataFrame from data collection
            symbols: List of symbols to analyze
            
        Returns:
            DataFrame with unified trading signals
        """
        all_signals = []
        
        # Import signal modules
        try:
            from signals.sentiment import analyze_sentiment_pipeline
            from signals.volume import analyze_volume_pipeline
            from signals.ta_triggers import analyze_technical_triggers_pipeline
            
            print("🔄 Processing all signal types...")
            
            # 1. Sentiment Analysis Signals
            print("📊 Analyzing sentiment...")
            try:
                sentiment_signals = analyze_sentiment_pipeline(input_df)
                if not sentiment_signals.empty:
                    sentiment_signals['signal_category'] = 'sentiment'
                    all_signals.append(sentiment_signals)
                    print(f"   ✅ Generated {len(sentiment_signals)} sentiment signals")
                else:
                    print("   ⚠️ No sentiment signals generated")
            except Exception as e:
                print(f"   ❌ Sentiment analysis error: {e}")
            
            # 2. Volume Analysis Signals
            print("📈 Analyzing volume patterns...")
            try:
                volume_signals = analyze_volume_pipeline(input_df, symbols)
                if not volume_signals.empty:
                    volume_signals['signal_category'] = 'volume'
                    all_signals.append(volume_signals)
                    print(f"   ✅ Generated {len(volume_signals)} volume signals")
                else:
                    print("   ⚠️ No volume signals generated")
            except Exception as e:
                print(f"   ❌ Volume analysis error: {e}")
            
            # 3. Technical Analysis Triggers
            print("🔧 Analyzing technical breakouts...")
            try:
                technical_signals = analyze_technical_triggers_pipeline(symbols)
                if not technical_signals.empty:
                    technical_signals['signal_category'] = 'technical'
                    all_signals.append(technical_signals)
                    print(f"   ✅ Generated {len(technical_signals)} technical signals")
                else:
                    print("   ⚠️ No technical signals generated")
            except Exception as e:
                print(f"   ❌ Technical analysis error: {e}")
            
        except ImportError as e:
            print(f"❌ Signal module import error: {e}")
            return pd.DataFrame()
        
        # Combine all signals
        if all_signals:
            combined_signals = pd.concat(all_signals, ignore_index=True)
            return self.generate_unified_signals(combined_signals)
        else:
            print("⚠️ No signals generated from any module")
            return pd.DataFrame()
    
    def generate_unified_signals(self, combined_signals: pd.DataFrame) -> pd.DataFrame:
        """
        Generate unified trading signals by combining all signal types.
        
        Args:
            combined_signals: Combined DataFrame from all signal modules
            
        Returns:
            DataFrame with unified trading decisions
        """
        if combined_signals.empty or 'symbol' not in combined_signals.columns:
            return pd.DataFrame()
        
        unified_signals = []
        
        # Group by symbol to create unified signals
        for symbol in combined_signals['symbol'].unique():
            symbol_signals = combined_signals[combined_signals['symbol'] == symbol]
            
            # Initialize unified signal
            unified_signal = {
                'symbol': symbol,
                'timestamp': pd.Timestamp.now(),
                'signal_source': 'unified_signal_engine'
            }
            
            # Categorize signals by type
            sentiment_signals = symbol_signals[symbol_signals['signal_category'] == 'sentiment']
            volume_signals = symbol_signals[symbol_signals['signal_category'] == 'volume']
            technical_signals = symbol_signals[symbol_signals['signal_category'] == 'technical']
            
            # Calculate weighted signal strength
            total_weight = 0
            weighted_score = 0
            
            # Sentiment component
            if not sentiment_signals.empty:
                avg_sentiment = sentiment_signals.get('sentiment_score', sentiment_signals.get('signal_strength', [0])).mean()
                weighted_score += avg_sentiment * self.signal_weights['sentiment_analysis']
                total_weight += self.signal_weights['sentiment_analysis']
                unified_signal['sentiment_score'] = avg_sentiment
                unified_signal['sentiment_signals_count'] = len(sentiment_signals)
            else:
                unified_signal['sentiment_score'] = 0.0
                unified_signal['sentiment_signals_count'] = 0
            
            # Volume component
            if not volume_signals.empty:
                # Volume signals typically use different scoring, normalize to -1 to +1
                volume_score = 0
                for _, vol_signal in volume_signals.iterrows():
                    if 'BUY' in str(vol_signal.get('signal_type', '')).upper():
                        volume_score += 0.5
                    elif 'SELL' in str(vol_signal.get('signal_type', '')).upper():
                        volume_score -= 0.5
                    
                    # Add momentum signals
                    momentum = vol_signal.get('momentum_signal', '')
                    if 'STRONG' in str(momentum).upper():
                        volume_score += 0.3 if volume_score >= 0 else -0.3
                    elif 'MODERATE' in str(momentum).upper():
                        volume_score += 0.2 if volume_score >= 0 else -0.2
                
                volume_score = max(-1, min(1, volume_score))  # Clamp to -1, +1
                weighted_score += volume_score * self.signal_weights['volume_analysis']
                total_weight += self.signal_weights['volume_analysis']
                unified_signal['volume_score'] = volume_score
                unified_signal['volume_signals_count'] = len(volume_signals)
            else:
                unified_signal['volume_score'] = 0.0
                unified_signal['volume_signals_count'] = 0
            
            # Technical component
            if not technical_signals.empty:
                technical_score = 0
                entry_triggers = 0
                
                for _, tech_signal in technical_signals.iterrows():
                    direction = str(tech_signal.get('direction', '')).upper()
                    strength = str(tech_signal.get('strength', '')).upper()
                    is_entry = tech_signal.get('entry_trigger', False)
                    
                    # Score based on direction and strength
                    if direction == 'BULLISH':
                        if strength == 'STRONG':
                            technical_score += 0.8
                        elif strength == 'MODERATE':
                            technical_score += 0.5
                        else:
                            technical_score += 0.3
                    elif direction == 'BEARISH':
                        if strength == 'STRONG':
                            technical_score -= 0.8
                        elif strength == 'MODERATE':
                            technical_score -= 0.5
                        else:
                            technical_score -= 0.3
                    
                    if is_entry:
                        entry_triggers += 1
                
                technical_score = max(-1, min(1, technical_score))  # Clamp to -1, +1
                weighted_score += technical_score * self.signal_weights['technical_analysis']
                total_weight += self.signal_weights['technical_analysis']
                unified_signal['technical_score'] = technical_score
                unified_signal['technical_signals_count'] = len(technical_signals)
                unified_signal['entry_triggers'] = entry_triggers
            else:
                unified_signal['technical_score'] = 0.0
                unified_signal['technical_signals_count'] = 0
                unified_signal['entry_triggers'] = 0
            
            # Calculate final unified score
            if total_weight > 0:
                final_score = weighted_score / total_weight
            else:
                final_score = 0.0
            
            unified_signal['unified_score'] = final_score
            unified_signal['total_signals'] = len(symbol_signals)
            
            # Generate trading decision
            trading_decision = self.generate_trading_decision(unified_signal, final_score)
            unified_signal.update(trading_decision)
            
            unified_signals.append(unified_signal)
        
        return pd.DataFrame(unified_signals)
    
    def generate_trading_decision(self, signal_data: Dict[str, Any], final_score: float) -> Dict[str, Any]:
        """
        Generate final trading decision with your risk management parameters.
        
        Args:
            signal_data: Unified signal data for the symbol
            final_score: Final weighted score (-1 to +1)
            
        Returns:
            Dict with trading decision and risk parameters
        """
        symbol = signal_data['symbol']
        
        # Get current price for position sizing
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            current_price = ticker.history(period="1d")['Close'].iloc[-1]
        except:
            current_price = 100.0  # Fallback price
        
        # Generate trading signal based on unified score
        if final_score >= 0.6:
            trade_signal = 'STRONG_BUY'
            position_size = 1.0  # Full position
        elif final_score >= 0.3:
            trade_signal = 'BUY'
            position_size = 0.75  # 75% position
        elif final_score <= -0.6:
            trade_signal = 'STRONG_SELL'
            position_size = 1.0  # Full short position
        elif final_score <= -0.3:
            trade_signal = 'SELL'
            position_size = 0.75  # 75% short position
        else:
            trade_signal = 'HOLD'
            position_size = 0.0
        
        # Calculate risk management levels (your exact parameters)
        entry_price = current_price
        stop_loss = entry_price * (1 + self.risk_params['stop_loss_pct'] / 100)
        take_profit = entry_price * (1 + self.risk_params['take_profit_pct'] / 100)
        partial_sell_level = take_profit  # Sell 50% at take profit
        
        return {
            'trading_signal': trade_signal,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'partial_sell_level': partial_sell_level,
            'partial_sell_pct': self.risk_params['partial_sell_pct'],
            'position_size': position_size,
            'risk_reward_ratio': abs(self.risk_params['take_profit_pct'] / self.risk_params['stop_loss_pct']),
            'confidence_level': abs(final_score)
        }

def run_complete_signal_engine(input_df: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
    """
    Main function to run the complete signal engine pipeline.
    
    Args:
        input_df: Your combined DataFrame from data collection
        symbols: List of symbols to analyze
        
    Returns:
        DataFrame with unified trading signals and risk management
    """
    print("🚀 RUNNING COMPLETE SIGNAL ENGINE")
    print("=" * 50)
    
    engine = SignalEngine()
    
    # Process all signals
    unified_signals = engine.process_all_signals(input_df, symbols)
    
    # Summary
    if not unified_signals.empty:
        print(f"\n🎯 SIGNAL ENGINE RESULTS")
        print("-" * 30)
        
        for _, signal in unified_signals.iterrows():
            print(f"📊 {signal['symbol']}: {signal['trading_signal']}")
            print(f"   Unified Score: {signal['unified_score']:.2f}")
            print(f"   Entry: ${signal['entry_price']:.2f}")
            print(f"   Stop Loss: ${signal['stop_loss']:.2f} ({signal['unified_score']:.1%})")
            print(f"   Take Profit: ${signal['take_profit']:.2f} ({signal['unified_score']:.1%})")
            print(f"   Signals Used: {signal['total_signals']} ({signal['sentiment_signals_count']}S + {signal['volume_signals_count']}V + {signal['technical_signals_count']}T)")
            print()
        
        print(f"✅ Generated {len(unified_signals)} unified trading decisions")
    else:
        print("⚠️ No unified signals generated")
    
    return unified_signals

# Integration example
if __name__ == "__main__":
    # Sample data for testing
    sample_data = pd.DataFrame({
        'symbol': ['TQQQ', 'SOXL', 'LABU'] * 3,
        'timestamp': [pd.Timestamp.now()] * 9,
        'source': ['reddit', 'news', 'yahoo_finance'] * 3,
        'text': [
            'TQQQ breaking out with massive volume! 🚀',
            'SOXL showing weakness in semiconductor sector',
            'LABU biotech momentum building strongly',
            'Market volatility increasing, caution advised',
            'Volume spikes across tech ETFs, momentum building',
            'Technical analysis suggests breakout incoming',
            'Bullish sentiment on leveraged ETFs',
            'Risk management crucial in current market',
            'High-leverage plays showing strong patterns'
        ]
    })
    
    symbols = ['TQQQ', 'SOXL', 'LABU']
    
    # Run complete signal engine
    results = run_complete_signal_engine(sample_data, symbols)
    
    if not results.empty:
        print("\n🔥 SIGNAL ENGINE OPERATIONAL!")
    else:
        print("\n⚠️ Signal engine needs debugging")
