import pandas as pd
import numpy as np

def detect_volume_spikes(df: pd.DataFrame) -> pd.DataFrame:
    """Detect simple volume spikes using z-score on recent window.
    Returns a DataFrame with volume_strength in [-1,1].
    """
    if df is None or df.empty or 'volume' not in df.columns:
        return pd.DataFrame()
    s = pd.to_numeric(df['volume'], errors='coerce').fillna(0.0).astype(float)
    if s.size < 5:
        return pd.DataFrame({'volume_strength': [0.0]})
    roll = s.rolling(20, min_periods=5)
    mean = roll.mean()
    std = roll.std().replace(0, 1)
    z = (s - mean) / std
    out = pd.DataFrame({'volume_strength': z.clip(-3, 3) / 3.0})
    return out.tail(1)
