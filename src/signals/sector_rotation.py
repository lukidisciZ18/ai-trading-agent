#!/usr/bin/env python3
"""
Simple Sector Rotation Analysis for 3x Leveraged ETFs

Compares underlying sector strength to help choose between TQQQ/SOXL/LABU.
Simple, effective, and directly relevant to your strategy.
"""

import pandas as pd
import yfinance as yf
from typing import Dict, List

def get_sector_rotation_signal() -> Dict[str, float]:
    """
    Simple sector rotation analysis for TQQQ/SOXL/LABU selection.
    
    Compares:
    - QQQ (Tech) vs SPY
    - SOXX (Semiconductors) vs SPY  
    - XBI (Biotech) vs SPY
    
    Returns:
        Dict with sector strength scores
    """
    try:
        # Download 10-day data for sectors and benchmark
        sectors = ['QQQ', 'SOXX', 'XBI', 'SPY']
        data = yf.download(sectors, period='11d', interval='1d', group_by='ticker')
        
        if data.empty:
            return _default_scores()
        
        # Calculate 10-day performance vs SPY
        scores = {}
        
        # Get SPY performance as benchmark
        spy_data = data['SPY']['Close'].dropna()
        if len(spy_data) >= 10:
            spy_return = float(spy_data.iloc[-1] / spy_data.iloc[-10] - 1)
        else:
            spy_return = 0.0
        
        # Compare each sector to SPY
        sector_map = {
            'QQQ': 'tech_score',     # For TQQQ
            'SOXX': 'semi_score',    # For SOXL  
            'XBI': 'bio_score'       # For LABU
        }
        
        for sector, score_name in sector_map.items():
            try:
                sector_data = data[sector]['Close'].dropna()
                if len(sector_data) >= 10:
                    sector_return = float(sector_data.iloc[-1] / sector_data.iloc[-10] - 1)
                    # Simple relative strength: sector return - SPY return
                    relative_strength = sector_return - spy_return
                    
                    # Convert to simple score
                    if relative_strength > 0.02:      # Outperforming by >2%
                        scores[score_name] = 1.0
                    elif relative_strength > -0.02:   # Similar performance
                        scores[score_name] = 0.0
                    else:                             # Underperforming by >2%
                        scores[score_name] = -1.0
                else:
                    scores[score_name] = 0.0
            except:
                scores[score_name] = 0.0
        
        # Find the strongest sector
        best_sector = max(scores.keys(), key=lambda k: scores[k])
        
        return {
            'tech_score': scores.get('tech_score', 0.0),
            'semi_score': scores.get('semi_score', 0.0), 
            'bio_score': scores.get('bio_score', 0.0),
            'strongest_sector': best_sector,
            'spy_return_10d': spy_return
        }
        
    except Exception as e:
        print(f"⚠️ Sector rotation error: {e}")
        return _default_scores()

def _default_scores():
    """Default neutral scores when data unavailable"""
    return {
        'tech_score': 0.0,
        'semi_score': 0.0,
        'bio_score': 0.0,
        'strongest_sector': 'tech_score',
        'spy_return_10d': 0.0
    }

def get_recommended_etf() -> str:
    """
    Simple recommendation: which 3x ETF looks best right now?
    
    Returns:
        'TQQQ', 'SOXL', or 'LABU'
    """
    rotation = get_sector_rotation_signal()
    
    # Simple mapping
    sector_to_etf = {
        'tech_score': 'TQQQ',
        'semi_score': 'SOXL', 
        'bio_score': 'LABU'
    }
    
    return sector_to_etf.get(rotation['strongest_sector'], 'TQQQ')

if __name__ == "__main__":
    print("🧪 Testing Simple Sector Rotation...")
    
    rotation = get_sector_rotation_signal()
    
    print()
    print('📊 Sector Strength vs SPY (10-day):')
    print(f'  Tech (QQQ): {rotation["tech_score"]:+.1f}')
    print(f'  Semiconductors (SOXX): {rotation["semi_score"]:+.1f}')
    print(f'  Biotech (XBI): {rotation["bio_score"]:+.1f}')
    
    print()
    recommended = get_recommended_etf()
    print(f'🎯 Strongest Sector: {rotation["strongest_sector"].replace("_score", "").title()}')
    print(f'💡 Recommended 3x ETF: {recommended}')
    
    print()
    print('🚀 Simple sector rotation for better 3x ETF selection!')
