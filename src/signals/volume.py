#!/usr/bin/env python3
"""
Volume Analysis Engine for AI Trading Agent

Clean volume spike detection using rolling median analysis.
Perfect for detecting momentum breakouts in your trading strategy.
"""

import pandas as pd
import yfinance as yf
from typing import List, Dict, Any

def detect_volume_spikes(price_df: pd.DataFrame, window: int = 20, threshold: float = 2.0) -> pd.DataFrame:
    """
    Given a price DataFrame with ['symbol', 'timestamp', 'volume'],
    flags rows where volume > threshold * rolling_median(volume).
    Returns DataFrame of spikes with columns ['symbol', 'timestamp', 'volume', 'rolling_med', 'spike'].
    
    Args:
        price_df: DataFrame with symbol, timestamp, volume columns
        window: Rolling window for median calculation (default: 20)
        threshold: Spike threshold multiplier (default: 2.0)
        
    Returns:
        DataFrame containing only volume spike events
    """
    # Ensure required columns exist
    if 'timestamp' not in price_df.columns:
        # Add timestamp if missing (for testing)
        df = price_df.copy()
        if len(df) > 0:
            df['timestamp'] = pd.date_range('2025-01-01', periods=len(df), freq='D')
    else:
        df = price_df.copy()
    
    df = df.sort_values(['symbol','timestamp']) if 'timestamp' in df.columns else df.copy()
    
    def compute(group):
        group = group.copy()  # Avoid SettingWithCopyWarning
        group['rolling_med'] = group['volume'].rolling(window, min_periods=1).median()
        group['spike'] = group['volume'] > (threshold * group['rolling_med'])
        return group
    
    out = df.groupby('symbol', group_keys=False).apply(compute).reset_index(drop=True)
    return out[out['spike']]


def get_volume_data(symbols: List[str], period: str = "60d") -> pd.DataFrame:
    """
    Fetch volume data from yfinance for volume spike analysis.
    
    Args:
        symbols: List of stock/ETF symbols
        period: Time period for data (default: "60d")
        
    Returns:
        DataFrame with symbol, timestamp, volume columns
    """
    all_data = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if not hist.empty:
                vol_data = pd.DataFrame({
                    'symbol': symbol,
                    'timestamp': hist.index,
                    'volume': hist['Volume'].values,
                    'price': hist['Close'].values
                })
                all_data.append(vol_data)
                
        except Exception as e:
            print(f"Error fetching volume data for {symbol}: {e}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


def analyze_volume_signals(symbols: List[str], window: int = 20, threshold: float = 2.0) -> pd.DataFrame:
    """
    Complete volume analysis pipeline for your trading symbols.
    
    Args:
        symbols: List of symbols to analyze
        window: Rolling window for spike detection
        threshold: Volume spike threshold
        
    Returns:
        DataFrame with volume spike signals and strength scores
    """
    # Get volume data
    volume_data = get_volume_data(symbols)
    
    if volume_data.empty:
        return pd.DataFrame()
    
    # Detect volume spikes
    spikes = detect_volume_spikes(volume_data, window, threshold)
    
    if spikes.empty:
        return pd.DataFrame()
    
    # Add signal strength based on spike magnitude
    spikes['spike_ratio'] = spikes['volume'] / spikes['rolling_med']
    spikes['signal_strength'] = spikes['spike_ratio'].apply(lambda x:
        3 if x >= 3.0 else  # Strong signal
        2 if x >= 2.5 else  # Moderate signal  
        1                   # Weak signal
    )
    
    # Get latest spike for each symbol
    latest_spikes = spikes.groupby('symbol').tail(1).reset_index(drop=True)
    
    return latest_spikes[['symbol', 'timestamp', 'volume', 'spike_ratio', 'signal_strength']]


# Example usage and testing
if __name__ == "__main__":
    # Test with your ETF symbols
    symbols = ['TQQQ', 'SOXL', 'LABU']
    
    print("🔍 Volume Spike Analysis Test")
    print("=" * 40)
    
    # Get volume data
    volume_data = get_volume_data(symbols, period="30d")
    print(f"📊 Collected volume data: {len(volume_data)} records")
    
    # Detect spikes
    if not volume_data.empty:
        spikes = detect_volume_spikes(volume_data, window=20, threshold=2.0)
        print(f"⚡ Volume spikes detected: {len(spikes)}")
        
        # Analyze signals
        signals = analyze_volume_signals(symbols)
        print(f"🎯 Volume signals: {len(signals)}")
        
        if not signals.empty:
            print("\n📈 Latest Volume Signals:")
            for _, signal in signals.iterrows():
                print(f"   {signal['symbol']}: {signal['spike_ratio']:.1f}x volume spike (strength: {signal['signal_strength']})")
    else:
        print("❌ No volume data available")
