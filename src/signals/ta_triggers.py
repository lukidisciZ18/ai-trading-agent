#!/usr/bin/env python3
"""
Technical Analysis Triggers Engine for AI Trading Agent

Clean TA-Lib based RSI and MACD trigger detection.
Perfect for momentum trading signal generation.
"""

import pandas as pd
import talib
import yfinance as yf
from typing import List, Dict, Any

def generate_ta_triggers(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a price DataFrame with ['symbol', 'timestamp', 'open', 'high', 'low', 'close'],
    compute RSI & MACD, and flag:
      - rsi_signal: RSI crossing above 30 (from oversold) or below 70 (from overbought)
      - macd_signal: MACD line crossing above its signal line.
    Returns DataFrame with columns:
      ['symbol','timestamp','rsi','macd','signal','rsi_signal','macd_signal'].
      
    Args:
        price_df: DataFrame with OHLC data
        
    Returns:
        DataFrame with technical analysis signals
    """
    # Handle missing timestamp column (for testing)
    df = price_df.copy()
    if 'timestamp' not in df.columns and len(df) > 0:
        df['timestamp'] = pd.date_range('2025-01-01', periods=len(df), freq='D')
    
    if 'timestamp' in df.columns:
        df = df.sort_values(['symbol','timestamp'])
    
    results = []

    for sym, group in df.groupby('symbol'):
        g = group.copy()
        
        # Calculate RSI and MACD using TA-Lib
        g['rsi'] = talib.RSI(g['close'], timeperiod=14)
        macd, signal, _ = talib.MACD(g['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        g['macd'] = macd
        g['signal'] = signal

        # Detect RSI crosses
        g['prev_rsi'] = g['rsi'].shift(1)
        g['rsi_signal'] = (
            ((g['prev_rsi'] < 30) & (g['rsi'] >= 30)).map({True: 'rsi_buy', False: None})
            .fillna(((g['prev_rsi'] > 70) & (g['rsi'] <= 70)).map({True: 'rsi_sell', False: None}))
        )

        # Detect MACD line crossing above signal
        g['prev_macd'] = g['macd'].shift(1)
        g['prev_signal'] = g['signal'].shift(1)
        g['macd_signal'] = (
            ((g['prev_macd'] < g['prev_signal']) & (g['macd'] > g['signal']))
            .map({True: 'macd_buy', False: None})
        )

        results.append(g)

    out = pd.concat(results, ignore_index=True)
    return out.drop(columns=['prev_rsi','prev_macd','prev_signal'])


def get_price_data(symbols: List[str], period: str = "60d") -> pd.DataFrame:
    """
    Fetch OHLC price data from yfinance for TA analysis.
    
    Args:
        symbols: List of stock/ETF symbols
        period: Time period for data (default: "60d")
        
    Returns:
        DataFrame with symbol, timestamp, OHLC columns
    """
    all_data = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if not hist.empty:
                price_data = pd.DataFrame({
                    'symbol': symbol,
                    'timestamp': hist.index,
                    'open': hist['Open'].values,
                    'high': hist['High'].values,
                    'low': hist['Low'].values,
                    'close': hist['Close'].values,
                    'volume': hist['Volume'].values
                })
                all_data.append(price_data)
                
        except Exception as e:
            print(f"Error fetching price data for {symbol}: {e}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


def analyze_ta_signals(symbols: List[str]) -> pd.DataFrame:
    """
    Complete technical analysis pipeline for your trading symbols.
    
    Args:
        symbols: List of symbols to analyze
        
    Returns:
        DataFrame with latest TA signals and current indicator values
    """
    # Get price data
    price_data = get_price_data(symbols)
    
    if price_data.empty:
        return pd.DataFrame()
    
    # Generate TA triggers
    ta_signals = generate_ta_triggers(price_data)
    
    if ta_signals.empty:
        return pd.DataFrame()
    
    # Get latest data for each symbol with current indicator values
    latest_data = ta_signals.groupby('symbol').tail(1).reset_index(drop=True)
    
    # Get latest signals (not None) for each symbol
    signal_data = []
    for symbol in symbols:
        sym_data = ta_signals[ta_signals['symbol'] == symbol]
        if sym_data.empty:
            continue
            
        latest = sym_data.iloc[-1]
        
        # Find latest RSI signal
        rsi_signals = sym_data[sym_data['rsi_signal'].notna()]
        latest_rsi_signal = rsi_signals.iloc[-1]['rsi_signal'] if not rsi_signals.empty else None
        
        # Find latest MACD signal
        macd_signals = sym_data[sym_data['macd_signal'].notna()]
        latest_macd_signal = macd_signals.iloc[-1]['macd_signal'] if not macd_signals.empty else None
        
        signal_data.append({
            'symbol': symbol,
            'timestamp': latest['timestamp'],
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'signal': latest['signal'],
            'latest_rsi_signal': latest_rsi_signal,
            'latest_macd_signal': latest_macd_signal,
            'signal_strength': (1 if latest_rsi_signal else 0) + (1 if latest_macd_signal else 0)
        })
    
    return pd.DataFrame(signal_data)


# Example usage and testing
if __name__ == "__main__":
    # Test with your ETF symbols
    symbols = ['TQQQ', 'SOXL', 'LABU']
    
    print("🔧 Technical Analysis Triggers Test")
    print("=" * 45)
    
    # Get price data
    price_data = get_price_data(symbols, period="30d")
    print(f"📊 Collected price data: {len(price_data)} records")
    
    # Generate TA triggers
    if not price_data.empty:
        ta_triggers = generate_ta_triggers(price_data)
        print(f"🎯 TA triggers generated: {len(ta_triggers)} records")
        
        # Analyze latest signals
        signals = analyze_ta_signals(symbols)
        print(f"📈 Latest signals: {len(signals)}")
        
        if not signals.empty:
            print("\n📊 Current Technical Analysis:")
            for _, signal in signals.iterrows():
                rsi = signal['rsi']
                macd = signal['macd']
                signal_line = signal['signal']
                latest_rsi = signal['latest_rsi_signal']
                latest_macd = signal['latest_macd_signal']
                
                print(f"   {signal['symbol']}:")
                print(f"      RSI: {rsi:.1f} (latest signal: {latest_rsi})")
                print(f"      MACD: {macd:.3f} vs Signal: {signal_line:.3f} (latest signal: {latest_macd})")
                print(f"      Combined strength: {signal['signal_strength']}")
                print()
    else:
        print("❌ No price data available")
