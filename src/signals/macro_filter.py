#!/usr/bin/env python3
"""
Simple Macro Filter for Leveraged ETF Trading

Provides simple, effective macro signals for 3x leveraged ETF timing.
Focus: VIX and underlying index momentum (perfect for TQQQ/SOXL/LABU).
"""

import pandas as pd
import yfinance as yf
from typing import Dict

def get_macro_signal() -> Dict[str, float]:
    """
    Simple macro filter for leveraged ETF trading.
    
    Returns:
        Dict with macro scores: vix_signal, momentum_signal, combined_score
    """
    try:
        # 1. VIX Signal (leverage works better in low volatility)
        vix_data = yf.download("^VIX", period="5d", interval="1d")
        if not vix_data.empty:
            current_vix = float(vix_data['Close'].iloc[-1])
            # Simple VIX scoring: lower VIX = better for leveraged ETFs
            if current_vix < 15:
                vix_signal = 1.0      # Low vol = good for leverage
            elif current_vix < 25:
                vix_signal = 0.0      # Medium vol = neutral
            else:
                vix_signal = -1.0     # High vol = bad for leverage
        else:
            vix_signal = 0.0
            current_vix = 0.0
        
        # 2. QQQ Momentum (drives TQQQ)
        qqq_data = yf.download("QQQ", period="10d", interval="1d")
        if not qqq_data.empty and len(qqq_data) >= 5:
            # Simple 5-day momentum
            recent_return = float(qqq_data['Close'].iloc[-1] / qqq_data['Close'].iloc[-5] - 1)
            if recent_return > 0.02:      # >2% in 5 days
                momentum_signal = 1.0
            elif recent_return > -0.02:   # Flat
                momentum_signal = 0.0
            else:                         # Down >2%
                momentum_signal = -1.0
        else:
            momentum_signal = 0.0
        
        # 3. Simple Combined Score
        combined_score = (vix_signal * 0.6) + (momentum_signal * 0.4)
        
        return {
            'vix_signal': vix_signal,
            'momentum_signal': momentum_signal,
            'combined_score': combined_score,
            'vix_level': current_vix
        }
        
    except Exception as e:
        print(f"⚠️ Macro filter error: {e}")
        return {
            'vix_signal': 0.0,
            'momentum_signal': 0.0,
            'combined_score': 0.0,
            'vix_level': 0
        }

def should_trade_leveraged_etfs() -> bool:
    """
    Simple go/no-go signal for leveraged ETF trading.
    
    Returns:
        True if macro conditions favor leveraged ETF trading
    """
    macro = get_macro_signal()
    
    # Simple rule: only trade leveraged ETFs when macro score > 0
    return macro['combined_score'] > 0

if __name__ == "__main__":
    print("🧪 Testing Simple Macro Filter...")
    
    macro_data = get_macro_signal()
    print()
    print('📊 Current Macro Conditions:')
    print(f'  VIX Signal: {macro_data["vix_signal"]:+.1f} (VIX Level: {macro_data["vix_level"]:.1f})')
    print(f'  QQQ Momentum: {macro_data["momentum_signal"]:+.1f}')
    print(f'  Combined Score: {macro_data["combined_score"]:+.2f}')
    
    print()
    should_trade = should_trade_leveraged_etfs()
    if should_trade:
        print('✅ GO: Macro conditions favor 3x ETF trading')
    else:
        print('❌ NO-GO: Wait for better macro conditions')
    
    print()
    print('🎯 Simple & effective macro timing for TQQQ/SOXL/LABU!')
