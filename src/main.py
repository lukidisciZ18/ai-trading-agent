#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime, timedelta
import os
import pandas as pd
from dotenv import load_dotenv

# load env
load_dotenv()

# allow relative imports
sys.path.insert(0, str(Path(__file__).parent))

from signals.sentiment import score_sentiment
from signals.volume import detect_volume_spikes
from signals.ta_triggers import generate_ta_triggers

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from data.fundamentals import fetch_overview, fetch_earnings, recent_earnings_date
from scheduler import build_scheduler, list_jobs

# Optional Alpha Vantage
try:
    from data.alpha_vantage import fetch_daily_ohlcv
except Exception:  # pragma: no cover
    fetch_daily_ohlcv = None  # type: ignore

# Helper to get recent texts per symbol from collected data
def _recent_texts_for_symbol(data_dir: Path, symbol: str, limit: int = 50) -> list[str]:
    p = data_dir / "trading_data_latest.csv"
    if not p.exists():
        return []
    try:
        df = pd.read_csv(p)
        df = df[df['symbol'] == symbol].tail(limit)
        return df['text'].astype(str).tolist()
    except Exception:
        return []

app = FastAPI(title="AI Trading Agent API", version="0.4")

class SignalRequest(BaseModel):
    symbols: list[str] | None = None
    strategy: str | None = None  # 'leveraged_etf' | 'momentum_smallcap'

class AITradingAgent:
    def __init__(self):
        self.symbols = ["TQQQ", "SOXL", "LABU"]
        self.data_path = Path(__file__).parent.parent / "data"
        self.scripts_path = Path(__file__).parent.parent / "scripts"
        self.strategies_path = Path(__file__).parent.parent / "strategies"
        self.config_path = Path(__file__).parent.parent / "config" / "settings.json"
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.alpha_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        # load config
        self.config = self._load_config()
        self.scheduler = None

    def _load_config(self) -> dict:
        try:
            import json
            if self.config_path.exists():
                return json.loads(self.config_path.read_text())
        except Exception:
            pass
        return {
            "min_price": 1.5,
            "min_10d_dollar_volume": 2_000_000,
            "earnings_window_days": 2,
            "biotech_catalyst_days": 14,
            "risk_pct": 0.005,
            "atr_k": 1.5,
            "sector_exclude": [],
            "sectors_biotech": ["Biotechnology", "Biotech", "Health Care", "Healthcare"],
            "account_equity": 10000,
        }

    def _latest_sentiment_path(self) -> Path:
        return self.data_path / "trading_data_latest.csv"

    def ensure_fresh_sentiment(self, max_age_minutes: int = 30) -> None:
        p = self._latest_sentiment_path()
        if not p.exists():
            self.collect_market_data()
            return
        try:
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            if datetime.now() - mtime > timedelta(minutes=max_age_minutes):
                self.collect_market_data()
        except Exception:
            self.collect_market_data()

    def collect_market_data(self) -> pd.DataFrame:
        try:
            sys.path.insert(0, str(self.scripts_path))
            from simple_data_collector import collect_all_data  # type: ignore
            df = collect_all_data(symbols=self.symbols, reddit_limit=5, news_limit=5, twitter_limit=5)
            if not df.empty:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                (self.data_path / f"trading_data_{ts}.csv").write_text(df.to_csv(index=False))
                (self.data_path / "trading_data_latest.csv").write_text(df.to_csv(index=False))
            return df
        except Exception:
            return pd.DataFrame()

    def get_symbol_data(self, symbol: str, prefer_alpha: bool = False) -> pd.DataFrame:
        # FAST_TEST mode: return deterministic synthetic OHLCV to avoid external calls in CI
        if os.getenv("FAST_TEST") == "1":
            import pandas as _pd
            now = datetime.utcnow()
            dates = _pd.date_range(end=now, periods=30, freq='D')
            base = 100.0
            closes = [base + (i * 0.1) for i in range(len(dates))]
            opens = [c * 0.995 for c in closes]
            highs = [c * 1.01 for c in closes]
            lows = [c * 0.99 for c in closes]
            vols = [100000 + i * 100 for i in range(len(dates))]
            df = _pd.DataFrame({
                'symbol': symbol,
                'timestamp': dates,
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': vols,
            })
            return df
        # Try Alpha Vantage if requested and key available; fallback to yfinance even if Alpha returns empty
        if prefer_alpha and self.alpha_key and fetch_daily_ohlcv:
            try:
                df_alpha = fetch_daily_ohlcv(symbol, self.alpha_key)
                if isinstance(df_alpha, pd.DataFrame) and not df_alpha.empty:
                    return df_alpha
            except Exception:
                # Will fallback to yfinance below
                pass
        try:
            import yfinance as yf
            df = yf.Ticker(symbol).history(period="60d").reset_index()
            if df.empty:
                return pd.DataFrame()
            df = df.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume', 'Date': 'timestamp'
            })
            df['symbol'] = symbol
            return df[['symbol','timestamp','open','high','low','close','volume']]
        except Exception:
            return pd.DataFrame()

    # Restored helper methods
    def get_sentiment_score(self, symbol: str) -> float:
        latest = self._latest_sentiment_path()
        if latest.exists():
            try:
                df = pd.read_csv(latest)
                df = df[df['symbol'] == symbol]
                if not df.empty and 'text' in df.columns:
                    return float(score_sentiment(df)['sentiment'].mean())
            except Exception:
                pass
        return 0.0

    def generate_technical_signals(self, symbol: str, prefer_alpha: bool = False) -> pd.DataFrame:
        data = self.get_symbol_data(symbol, prefer_alpha=prefer_alpha)
        if data.empty:
            return pd.DataFrame()
        return generate_ta_triggers(data)

    def analyze_volume_patterns(self, symbol: str, prefer_alpha: bool = False) -> pd.DataFrame:
        data = self.get_symbol_data(symbol, prefer_alpha=prefer_alpha)
        if data.empty:
            return pd.DataFrame()
        return detect_volume_spikes(data)

    def calculate_combined_signal_score(self, base_signal: float, ta_df: pd.DataFrame, vol_df: pd.DataFrame, sent: float) -> dict:
        weights = {'base':0.35,'technical':0.3,'volume':0.2,'sentiment':0.15}
        tech = float(ta_df['signal_strength'].mean()) if not ta_df.empty and 'signal_strength' in ta_df.columns else 0.0
        vol = float(vol_df['volume_strength'].mean()) if not vol_df.empty and 'volume_strength' in vol_df.columns else 0.0
        total = base_signal*weights['base'] + tech*weights['technical'] + vol*weights['volume'] + sent*weights['sentiment']
        action = 'BUY' if total > 0.6 else ('SELL' if total < -0.6 else 'HOLD')
        return {'total_score': total, 'action': action, 'technical_score': tech, 'volume_score': vol, 'confidence': min(abs(total),1.0)}

    # Filters and sizing helpers
    def _atr(self, df: pd.DataFrame, period: int = 14) -> float:
        try:
            if df.empty or not set(['high','low','close']).issubset(df.columns):
                return 0.0
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            prev_close = close.shift(1)
            tr = pd.concat([
                (high - low),
                (high - prev_close).abs(),
                (low - prev_close).abs()
            ], axis=1).max(axis=1)
            atr = tr.rolling(period, min_periods=period//2).mean().iloc[-1]
            return float(atr) if pd.notna(atr) else 0.0
        except Exception:
            return 0.0

    def _avg_dollar_volume(self, df: pd.DataFrame, lookback: int = 10) -> float:
        try:
            if df.empty or not set(['close','volume']).issubset(df.columns):
                return 0.0
            dol = (df['close'].astype(float) * df['volume'].astype(float)).rolling(lookback, min_periods=max(3, lookback//2)).mean().iloc[-1]
            return float(dol) if pd.notna(dol) else 0.0
        except Exception:
            return 0.0

    def _apply_filters(self, symbol: str, df: pd.DataFrame, sector: str | None = None, has_recent_biotech_catalyst: bool | None = None) -> tuple[bool, dict]:
        meta: dict = {"filters": []}
        cfg = self.config
        if df.empty:
            meta["filters"].append("no_data")
            return False, meta
        # price guard (prefer universe_guards.price_min if set)
        ug = cfg.get("universe_guards", {}) if isinstance(cfg.get("universe_guards"), dict) else {}
        price_min = float(ug.get("price_min", cfg.get("min_price", 1.0)))
        price = float(df['close'].iloc[-1])
        if price < price_min:
            meta["filters"].append("min_price")
            return False, meta
        # dollar volume guard (legacy)
        adv = self._avg_dollar_volume(df, 10)
        if adv < cfg.get("min_10d_dollar_volume", 0):
            meta["filters"].append("min_dollar_vol")
            return False, meta
        # raw volume guard (new, if configured)
        min_avg_vol = ug.get("min_avg_volume")
        if min_avg_vol is not None:
            try:
                avg_vol = float(df['volume'].astype(float).rolling(10, min_periods=5).mean().iloc[-1])
                if pd.notna(avg_vol) and avg_vol < float(min_avg_vol):
                    meta["filters"].append("min_avg_volume")
                    return False, meta
            except Exception:
                pass
        # sector exclude
        if sector and sector in set(cfg.get("sector_exclude", [])):
            meta["filters"].append("sector_exclude")
            return False, meta
        # biotech hygiene (if classified as biotech-like)
        if sector and sector in set(cfg.get("sectors_biotech", [])):
            if not has_recent_biotech_catalyst:
                meta["filters"].append("biotech_no_catalyst")
                return False, meta
        return True, meta

    def _position_size(self, account_equity: float, atr: float) -> float:
        cfg = self.config
        # prefer risk_params.max_risk_pct_per_trade, fallback to legacy risk_pct
        rp = cfg.get("risk_params", {}) if isinstance(cfg.get("risk_params"), dict) else {}
        risk = float(rp.get("max_risk_pct_per_trade", cfg.get("risk_pct", 0.005)))
        k = float(cfg.get("atr_k", 1.5))
        if atr <= 0:
            return 0.0
        return float((account_equity * risk) / (atr * k))

    def leveraged_etf_signals(self, symbols: list[str] | None = None) -> pd.DataFrame:
        # Ensure sentiment fresh for ETFs as well
        self.ensure_fresh_sentiment()
        # Advanced strategy for leveraged ETFs
        syms = symbols or self.symbols
        sys.path.insert(0, str(self.strategies_path))
        from leveraged_etf_strategy import score_leveraged_etf  # type: ignore
        rows = []
        for sym in syms:
            dfp = self.get_symbol_data(sym, prefer_alpha=False)
            base = score_leveraged_etf(dfp)
            ta = self.generate_technical_signals(sym, prefer_alpha=False)
            vol = self.analyze_volume_patterns(sym, prefer_alpha=False)
            sent = self.get_sentiment_score(sym)
            comb = self.calculate_combined_signal_score(base, ta, vol, sent)
            rows.append({
                'symbol': sym,
                'strength': base,
                'action': 'BUY' if base>0.5 else ('SELL' if base<-0.5 else 'HOLD'),
                'enhanced_strength': comb['total_score'],
                'enhanced_action': comb['action'],
                'confidence': comb['confidence']
            })
        out = pd.DataFrame(rows)
        out = out.fillna(0)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        out.to_csv(self.data_path / f"trading_signals_{ts}.csv", index=False)
        out.to_csv(self.data_path / "trading_signals_latest.csv", index=False)
        return out

    def momentum_smallcap_signals(self, symbols: list[str]) -> pd.DataFrame:
        # Ensure sentiment is fresh before computing signals
        self.ensure_fresh_sentiment()
        if not symbols:
            return pd.DataFrame()
        sys.path.insert(0, str(self.strategies_path))
        from momentum_smallcap_strategy import score_smallcap_momentum, trade_plan  # type: ignore
        rows = []
        for sym in symbols:
            dfp = self.get_symbol_data(sym, prefer_alpha=True)
            sent = self.get_sentiment_score(sym)
            texts = _recent_texts_for_symbol(self.data_path, sym, limit=100)
            fmeta = self.fundamentals_meta(sym)
            sector = fmeta.get('sector')
            last_earn = fmeta.get('last_earnings_date')
            # earnings window filter (skip if within configured window)
            earn_block = False
            try:
                wnd = int(self.config.get('earnings_window_days', 0))
                if last_earn and wnd > 0:
                    from datetime import datetime as _dt
                    if (datetime.now() - _dt.fromisoformat(str(last_earn))).days <= wnd:
                        earn_block = True
            except Exception:
                pass
            has_recent_bio_cat = not earn_block  # placeholder logic
            base = score_smallcap_momentum(dfp, sentiment=sent, texts=texts)
            ok, meta = self._apply_filters(sym, dfp, sector=sector, has_recent_biotech_catalyst=has_recent_bio_cat)
            if earn_block:
                meta.setdefault('filters', []).append('earnings_window')
                ok = False
            meta.update({k: v for k, v in fmeta.items() if k not in meta})
            if not ok:
                entry = float(dfp['close'].tail(1).iloc[0]) if not dfp.empty else 0.0
                rows.append({
                    'symbol': sym,
                    'strength': base,
                    'action': 'HOLD',
                    'enhanced_strength': 0.0,
                    'enhanced_action': 'HOLD',
                    'confidence': 0.0,
                    'entry_price': entry,
                    'risk_plan': {},
                    'position_size': 0.0,
                    'atr': 0.0,
                    'meta': meta,
                })
                continue
            ta = generate_ta_triggers(dfp) if not dfp.empty else pd.DataFrame()
            vol = detect_volume_spikes(dfp) if not dfp.empty else pd.DataFrame()
            comb = self.calculate_combined_signal_score(base, ta, vol, sent)
            entry = float(dfp['close'].tail(1).iloc[0]) if not dfp.empty else 0.0
            # risk params
            rp = self.config.get('risk_params', {}) if isinstance(self.config.get('risk_params'), dict) else {}
            sl_pct = float(rp.get('stop_loss_pct', 0.08))
            tp_pct = float(rp.get('take_profit_pct', 0.20))
            tr_pct = float(rp.get('trail_pct', 0.08))
            plan = trade_plan(entry, stop_loss_pct=sl_pct, take_profit_pct=tp_pct, trail_pct=tr_pct) if entry > 0 else {}
            atr_val = self._atr(dfp)
            size = self._position_size(account_equity=float(self.config.get('account_equity', 10000)), atr=atr_val)
            rows.append({
                'symbol': sym,
                'strength': base,
                'action': 'BUY' if base>0.5 else ('SELL' if base<-0.5 else 'HOLD'),
                'enhanced_strength': comb['total_score'],
                'enhanced_action': comb['action'],
                'confidence': comb['confidence'],
                'entry_price': entry,
                'risk_plan': plan,
                'position_size': size,
                'atr': atr_val,
                'meta': meta,
            })
        out = pd.DataFrame(rows)
        out = out.fillna(0)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        out.to_csv(self.data_path / f"trading_signals_{ts}.csv", index=False)
        out.to_csv(self.data_path / "trading_signals_latest.csv", index=False)
        return out

    def generate_trading_signals(self) -> pd.DataFrame:
        # default keeps backward-compatible simple signals for the 3 ETFs
        return self.leveraged_etf_signals(self.symbols)

    def fundamentals_meta(self, symbol: str) -> dict:
        meta: dict = {}
        ov = fetch_overview(symbol)
        er = fetch_earnings(symbol)
        if ov:
            meta['sector'] = ov.get('Sector') or ov.get('Industry')
            meta['market_cap'] = ov.get('MarketCapitalization')
        if er:
            meta['last_earnings_date'] = recent_earnings_date(er)
        return meta

agent_singleton = AITradingAgent()

@app.on_event("startup")
async def on_start():
    # start scheduler
    agent_singleton.scheduler = build_scheduler(
        scan_func=lambda mode: None,
        sentiment_func=lambda: agent_singleton.ensure_fresh_sentiment(),
    )
    agent_singleton.scheduler.start()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/signals")
def get_signals(strategy: str = Query(default="leveraged_etf"), symbols: str | None = Query(default=None)):
    try:
        syms = [s.strip().upper() for s in symbols.split(',')] if symbols else None
        if strategy == 'momentum_smallcap':
            if not syms:
                return JSONResponse({"error": "symbols required for momentum_smallcap"}, status_code=400)
            df = agent_singleton.momentum_smallcap_signals(syms)
        else:
            df = agent_singleton.leveraged_etf_signals(syms or agent_singleton.symbols)
        return JSONResponse(df.to_dict(orient='records'))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/signals")
def post_signals(body: SignalRequest):
    strategy = (body.strategy or 'leveraged_etf').lower()
    syms = [s.strip().upper() for s in (body.symbols or agent_singleton.symbols)]
    try:
        if strategy == 'momentum_smallcap':
            df = agent_singleton.momentum_smallcap_signals(syms)
        else:
            df = agent_singleton.leveraged_etf_signals(syms)
        return JSONResponse(df.to_dict(orient='records'))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/rescan")
def rescan(body: SignalRequest):
    strategy = (body.strategy or 'momentum_smallcap').lower()
    syms = [s.strip().upper() for s in (body.symbols or [])]
    if not syms:
        return JSONResponse({"error": "symbols required"}, status_code=400)
    try:
        if strategy == 'leveraged_etf':
            df = agent_singleton.leveraged_etf_signals(syms)
        else:
            df = agent_singleton.momentum_smallcap_signals(syms)
        return JSONResponse(df.to_dict(orient='records'))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/schedule")
def schedule():
    if not agent_singleton.scheduler:
        return {"jobs": []}
    return {"jobs": list_jobs(agent_singleton.scheduler)}

# CLI entry remains for container CMD --mode api by default in Docker
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['run','test','collect','signals','api'], default='api')
    p.add_argument('--strategy', choices=['leveraged_etf','momentum_smallcap'], default='leveraged_etf')
    p.add_argument('--symbols', type=str, default='')
    a = p.parse_args()
    if a.mode == 'api':
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
    elif a.mode == 'signals':
        agent = AITradingAgent()
        syms = [s.strip().upper() for s in a.symbols.split(',') if s.strip()] or None
        if a.strategy == 'momentum_smallcap':
            print(agent.momentum_smallcap_signals(syms or []))
        else:
            print(agent.leveraged_etf_signals(syms or agent.symbols))
    elif a.mode == 'collect':
        agent = AITradingAgent()
        agent.collect_market_data()
    else:
        agent = AITradingAgent()
        agent.generate_trading_signals()
