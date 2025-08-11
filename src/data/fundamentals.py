"""Fundamental data helpers (Alpha Vantage) with simple in‑memory TTL cache.
Safe fallbacks (return empty dict) if API key missing or errors occur.
"""
from __future__ import annotations
import os, time
from typing import Any, Dict
import httpx
from tenacity import retry, wait_random_exponential, stop_after_attempt

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"
_TTL_SECONDS = 3600  # 1h
_cache: dict[str, tuple[float, dict]] = {}


def _cache_get(k: str) -> dict | None:
    v = _cache.get(k)
    if not v:
        return None
    ts, data = v
    if time.time() - ts > _TTL_SECONDS:
        _cache.pop(k, None)
        return None
    return data


def _cache_set(k: str, data: dict) -> None:
    _cache[k] = (time.time(), data)


@retry(wait=wait_random_exponential(multiplier=1, max=30), stop=stop_after_attempt(3), reraise=False)
def fetch_overview(symbol: str) -> Dict[str, Any]:
    if not API_KEY:
        return {}
    key = f"overview:{symbol}"
    if (c := _cache_get(key)):
        return c
    params = {"function": "OVERVIEW", "symbol": symbol, "apikey": API_KEY}
    try:
        with httpx.Client(timeout=15) as client:
            r = client.get(BASE_URL, params=params)
        if r.status_code != 200:
            return {}
        data = r.json()
        if isinstance(data, dict) and data.get("Symbol"):
            _cache_set(key, data)
            return data
    except Exception:
        return {}
    return {}


@retry(wait=wait_random_exponential(multiplier=1, max=30), stop=stop_after_attempt(3), reraise=False)
def fetch_earnings(symbol: str) -> Dict[str, Any]:
    if not API_KEY:
        return {}
    key = f"earnings:{symbol}"
    if (c := _cache_get(key)):
        return c
    params = {"function": "EARNINGS", "symbol": symbol, "apikey": API_KEY}
    try:
        with httpx.Client(timeout=15) as client:
            r = client.get(BASE_URL, params=params)
        if r.status_code != 200:
            return {}
        data = r.json()
        if isinstance(data, dict):
            _cache_set(key, data)
            return data
    except Exception:
        return {}
    return {}


def recent_earnings_date(earnings_json: dict) -> str | None:
    """Return most recent reportedDate from quarterlyEarnings, if present."""
    try:
        qe = earnings_json.get("quarterlyEarnings")
        if isinstance(qe, list) and qe:
            # Alpha Vantage returns newest first
            return qe[0].get("reportedDate")
    except Exception:
        return None
    return None
