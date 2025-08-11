from __future__ import annotations
import pandas as pd

class TradingSignalGenerator:
    def generate_etf_signals(self, symbols: list[str]) -> pd.DataFrame:
        # Placeholder: simple base strengths
        strengths = [0.7, 0.1, -0.2]
        actions = ['BUY','HOLD','SELL']
        return pd.DataFrame({'symbol': symbols, 'strength': strengths[:len(symbols)], 'action': actions[:len(symbols)]})

# New advanced strategies live in separate modules:
# - strategies/leveraged_etf_strategy.py
# - strategies/momentum_smallcap_strategy.py
