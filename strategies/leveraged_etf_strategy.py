from __future__ import annotations
import pandas as pd

# Scoring for leveraged ETFs (TQQQ, SOXL, LABU):
# - Look for MA cross and RSI-like momentum (approx without TA-Lib)

def score_leveraged_etf(df: pd.DataFrame) -> float:
    if df is None or df.empty or 'close' not in df.columns:
        return 0.0
    s = df['close'].astype(float)
    ma_fast = s.rolling(5, min_periods=3).mean()
    ma_slow = s.rolling(20, min_periods=5).mean()
    momentum = (s.pct_change(3)).fillna(0).tail(1).iloc[0]
    cross = 1.0 if (ma_fast.tail(1).iloc[0] > ma_slow.tail(1).iloc[0]) else -1.0
    base = 0.6*cross + 0.4*max(min(momentum*10,1.0), -1.0)
    return float(max(min(base, 1.0), -1.0))
