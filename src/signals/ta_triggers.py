import pandas as pd

# Lightweight TA without TA-Lib, using pandas-ta if available, else simple MA crossover.
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except Exception:
    HAS_PANDAS_TA = False

def generate_ta_triggers(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or 'close' not in df.columns:
        return pd.DataFrame()
    close = df['close'].astype(float)
    if HAS_PANDAS_TA:
        rsi = ta.rsi(close, length=14)
        macd = ta.macd(close)
        score = 0.0
        if rsi is not None:
            last_rsi = float(rsi.dropna().tail(1).values[-1]) if not rsi.dropna().empty else 50.0
            score += (50 - abs(last_rsi - 50)) / 50.0  # favor mid RSI
        if macd is not None and 'MACD_12_26_9' in macd.columns:
            macd_last = float(macd['MACD_12_26_9'].dropna().tail(1).values[-1])
            score += max(min(macd_last / 2.0, 1.0), -1.0)
        return pd.DataFrame({'signal_strength': [max(min(score,1.0),-1.0)]})
    else:
        ma_fast = close.rolling(10, min_periods=3).mean()
        ma_slow = close.rolling(30, min_periods=5).mean()
        last = len(close) - 1
        if last <= 0:
            return pd.DataFrame()
        cross = 0
        if ma_fast.iloc[last] > ma_slow.iloc[last]:
            cross = 1
        elif ma_fast.iloc[last] < ma_slow.iloc[last]:
            cross = -1
        return pd.DataFrame({'signal_strength': [float(cross)]})
