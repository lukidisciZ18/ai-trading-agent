from __future__ import annotations
import pandas as pd
from typing import Dict

from signals.catalyst import catalyst_score

# Momentum for small-cap/micro-cap with sentiment + catalyst
# - Price breakout strength + volume expansion + catalyst boost
# - Returns a base score used by main to compute enhanced score

def score_smallcap_momentum(df: pd.DataFrame, sentiment: float = 0.0, texts: list[str] | None = None) -> float:
    if df is None or df.empty or 'close' not in df.columns or 'volume' not in df.columns:
        return 0.0
    s = df['close'].astype(float)
    v = df['volume'].astype(float)
    ret_5 = (s.pct_change(5)).fillna(0).tail(1).iloc[0]
    hi_20 = s.rolling(20, min_periods=5).max().tail(1).iloc[0]
    breakout = 1.0 if s.tail(1).iloc[0] >= hi_20 else -0.2
    v_z = ((v - v.rolling(20, min_periods=5).mean()) / (v.rolling(20, min_periods=5).std().replace(0,1))).clip(-3,3).tail(1).iloc[0]
    vol_score = float(v_z/3.0)
    cat = catalyst_score(texts or [])
    base = 0.45*max(min(ret_5*10,1.0),-1.0) + 0.3*breakout + 0.15*vol_score + 0.10*max(min(sentiment,1.0),-1.0)
    base += 0.15*cat
    return float(max(min(base, 1.0), -1.0))


def trade_plan(entry_price: float, stop_loss_pct: float = 0.08, take_profit_pct: float = 0.20, trail_pct: float = 0.08) -> Dict[str, float]:
    # Configurable: SL below entry; TP1 above entry; trailing after TP1
    return {
        "stop_loss": round(entry_price * (1.0 - stop_loss_pct), 4),
        "take_profit_1": round(entry_price * (1.0 + take_profit_pct), 4),
        "trail_after_tp1": float(trail_pct),
    }
