#!/usr/bin/env python3
"""
ETF Premium/Discount Monitor

Simple and effective tracking of 3x leveraged ETF premiums and discounts
to their theoretical NAV values. Critical for timing entries and exits.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional


def get_etf_premium_discount() -> Dict:
    """
    Monitor TQQQ, SOXL, LABU premium/discount to theoretical 3x values.
    
    Returns:
        Dict with premium/discount analysis for each 3x ETF
    """
    try:
        # Define ETF pairs: leveraged ETF -> underlying index
        etf_pairs = {
            'TQQQ': 'QQQ',    # 3x Tech
            'SOXL': 'SOXX',   # 3x Semiconductors  
            'LABU': 'XBI'     # 3x Biotech
        }
        
        results = {}
        
        for leveraged_etf, underlying_etf in etf_pairs.items():
            premium_data = calculate_premium_discount(leveraged_etf, underlying_etf)
            results[leveraged_etf] = premium_data
        
        # Overall signal
        overall_signal = analyze_overall_premium_discount(results)
        results['overall'] = overall_signal
        
        return results
        
    except Exception as e:
        print(f"⚠️ Error in ETF premium/discount analysis: {e}")
        return {
            'TQQQ': {'premium_discount': 0, 'signal': 0, 'status': 'ERROR'},
            'SOXL': {'premium_discount': 0, 'signal': 0, 'status': 'ERROR'},
            'LABU': {'premium_discount': 0, 'signal': 0, 'status': 'ERROR'},
            'overall': {'signal': 0, 'recommendation': 'HOLD'}
        }


def calculate_premium_discount(leveraged_etf: str, underlying_etf: str, leverage: float = 3.0) -> Dict:
    """
    Calculate premium/discount of leveraged ETF vs theoretical 3x value.
    
    Args:
        leveraged_etf: Symbol of 3x ETF (e.g., 'TQQQ')
        underlying_etf: Symbol of underlying ETF (e.g., 'QQQ')
        leverage: Leverage factor (default 3.0)
    
    Returns:
        Dict with premium/discount percentage and trading signal
    """
    try:
        # Get current prices
        lev_ticker = yf.Ticker(leveraged_etf)
        und_ticker = yf.Ticker(underlying_etf)
        
        # Get recent price data (5 days to calculate momentum)
        lev_data = lev_ticker.history(period="5d")
        und_data = und_ticker.history(period="5d")
        
        if lev_data.empty or und_data.empty:
            return {'premium_discount': 0, 'signal': 0, 'status': 'NO_DATA'}
        
        # Current prices
        lev_price = lev_data['Close'].iloc[-1]
        und_price = und_data['Close'].iloc[-1]
        
        # Calculate daily returns for both
        lev_returns = lev_data['Close'].pct_change().dropna()
        und_returns = und_data['Close'].pct_change().dropna()
        
        if len(lev_returns) < 2 or len(und_returns) < 2:
            return {'premium_discount': 0, 'signal': 0, 'status': 'INSUFFICIENT_DATA'}
        
        # Calculate actual vs theoretical tracking
        # Compare actual leveraged ETF return vs 3x underlying return
        actual_return = lev_returns.iloc[-1]  # Most recent daily return
        theoretical_return = und_returns.iloc[-1] * leverage
        
        # Premium/discount based on tracking difference
        tracking_difference = actual_return - theoretical_return
        
        # Convert to percentage points
        premium_discount_pct = tracking_difference * 100
        
        # Generate trading signal based on premium/discount
        signal = generate_premium_signal(premium_discount_pct, leveraged_etf)
        
        # Calculate average tracking over recent period
        if len(lev_returns) >= 3 and len(und_returns) >= 3:
            avg_tracking_diff = (lev_returns.iloc[-3:] - und_returns.iloc[-3:] * leverage).mean() * 100
        else:
            avg_tracking_diff = premium_discount_pct
        
        return {
            'premium_discount': round(premium_discount_pct, 3),
            'avg_tracking_diff': round(avg_tracking_diff, 3),
            'signal': signal,
            'status': 'OK',
            'lev_price': round(lev_price, 2),
            'und_price': round(und_price, 2),
            'actual_return': round(actual_return * 100, 2),
            'theoretical_return': round(theoretical_return * 100, 2)
        }
        
    except Exception as e:
        print(f"⚠️ Error calculating premium/discount for {leveraged_etf}: {e}")
        return {'premium_discount': 0, 'signal': 0, 'status': 'ERROR'}


def generate_premium_signal(premium_discount_pct: float, etf_symbol: str) -> int:
    """
    Generate trading signal based on premium/discount levels.
    
    Returns:
        +2: Strong buy (trading at discount)
        +1: Buy (moderate discount)  
         0: Neutral (fair value)
        -1: Sell (moderate premium)
        -2: Strong sell (excessive premium)
    """
    # Thresholds for premium/discount signals
    # Negative = discount (good to buy), Positive = premium (avoid/sell)
    
    if premium_discount_pct <= -0.5:    # >0.5% discount
        return 2  # Strong buy
    elif premium_discount_pct <= -0.2:  # 0.2-0.5% discount
        return 1  # Buy
    elif premium_discount_pct >= 0.5:   # >0.5% premium
        return -2  # Strong sell
    elif premium_discount_pct >= 0.2:   # 0.2-0.5% premium
        return -1  # Sell
    else:
        return 0  # Neutral (-0.2% to +0.2%)


def analyze_overall_premium_discount(results: Dict) -> Dict:
    """
    Analyze overall ETF premium/discount situation for trading decisions.
    
    Returns:
        Dict with overall signal and recommendations
    """
    try:
        valid_results = {k: v for k, v in results.items() 
                        if k != 'overall' and v.get('status') == 'OK'}
        
        if not valid_results:
            return {'signal': 0, 'recommendation': 'HOLD', 'status': 'NO_DATA'}
        
        # Calculate average signal and premium/discount
        signals = [v['signal'] for v in valid_results.values()]
        premiums = [v['premium_discount'] for v in valid_results.values()]
        
        avg_signal = sum(signals) / len(signals)
        avg_premium = sum(premiums) / len(premiums)
        
        # Generate recommendation
        if avg_signal >= 1.5:
            recommendation = 'STRONG_BUY'
            message = 'Multiple ETFs trading at discount'
        elif avg_signal >= 0.5:
            recommendation = 'BUY'
            message = 'ETFs trading below fair value'
        elif avg_signal <= -1.5:
            recommendation = 'STRONG_SELL'
            message = 'Multiple ETFs at premium'
        elif avg_signal <= -0.5:
            recommendation = 'SELL'
            message = 'ETFs trading above fair value'
        else:
            recommendation = 'HOLD'
            message = 'ETFs near fair value'
        
        return {
            'signal': round(avg_signal, 2),
            'avg_premium_discount': round(avg_premium, 3),
            'recommendation': recommendation,
            'message': message,
            'status': 'OK'
        }
        
    except Exception as e:
        print(f"⚠️ Error in overall premium/discount analysis: {e}")
        return {'signal': 0, 'recommendation': 'HOLD', 'status': 'ERROR'}


def get_best_etf_value() -> Tuple[str, Dict]:
    """
    Find the ETF with the best value (largest discount or smallest premium).
    
    Returns:
        Tuple of (best_etf_symbol, etf_data)
    """
    try:
        all_data = get_etf_premium_discount()
        
        # Filter valid data
        valid_etfs = {k: v for k, v in all_data.items() 
                     if k != 'overall' and v.get('status') == 'OK'}
        
        if not valid_etfs:
            return ('TQQQ', {'message': 'No data available'})
        
        # Find ETF with most negative premium/discount (biggest discount)
        best_etf = min(valid_etfs.keys(), 
                      key=lambda x: valid_etfs[x]['premium_discount'])
        
        return (best_etf, valid_etfs[best_etf])
        
    except Exception as e:
        print(f"⚠️ Error finding best ETF value: {e}")
        return ('TQQQ', {'message': 'Error in analysis'})


# Test function
def test_etf_premium_discount():
    """Test the ETF premium/discount monitoring system."""
    print("🧪 Testing ETF Premium/Discount Monitor...")
    print("=" * 50)
    
    # Test individual ETF analysis
    print("1. Individual ETF Analysis:")
    tqqq_data = calculate_premium_discount('TQQQ', 'QQQ')
    print(f"   TQQQ vs 3x QQQ: {tqqq_data}")
    
    # Test overall analysis
    print("\n2. Overall Premium/Discount Analysis:")
    overall_data = get_etf_premium_discount()
    
    for etf, data in overall_data.items():
        if etf != 'overall':
            premium = data.get('premium_discount', 0)
            signal = data.get('signal', 0)
            status = data.get('status', 'UNKNOWN')
            
            if status == 'OK':
                if premium > 0:
                    print(f"   {etf}: {premium:+.2f}% PREMIUM (signal: {signal:+1})")
                else:
                    print(f"   {etf}: {premium:+.2f}% DISCOUNT (signal: {signal:+1})")
            else:
                print(f"   {etf}: {status}")
    
    # Overall recommendation
    overall = overall_data.get('overall', {})
    if overall.get('status') == 'OK':
        rec = overall.get('recommendation', 'HOLD')
        msg = overall.get('message', '')
        print(f"\n📊 Overall: {rec} - {msg}")
    
    # Best value ETF
    print("\n3. Best Value ETF:")
    best_etf, best_data = get_best_etf_value()
    if 'premium_discount' in best_data:
        prem = best_data['premium_discount']
        print(f"   Best Value: {best_etf} ({prem:+.2f}% vs theoretical)")
    
    print("\n✅ ETF Premium/Discount Monitor Test Complete!")


if __name__ == "__main__":
    test_etf_premium_discount()
