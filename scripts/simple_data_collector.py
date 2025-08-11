from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import List
import requests
import pandas as pd

# -------- Reddit (PRAW) --------

def _fetch_reddit(symbol: str, limit: int = 5) -> list[dict]:
    cid = os.getenv("REDDIT_CLIENT_ID")
    csecret = os.getenv("REDDIT_CLIENT_SECRET")
    uagent = os.getenv("REDDIT_USER_AGENT", "ai-trading-agent/0.1")
    if not cid or not csecret:
        return []
    try:
        import praw  # type: ignore
        reddit = praw.Reddit(
            client_id=cid,
            client_secret=csecret,
            user_agent=uagent,
        )
        posts = []
        for sub in ["stocks", "wallstreetbets", "investing"]:
            for s in reddit.subreddit(sub).search(symbol, limit=limit, sort="new"):
                posts.append({
                    "symbol": symbol,
                    "timestamp": datetime.fromtimestamp(getattr(s, "created_utc", datetime.now().timestamp()), tz=timezone.utc),
                    "text": f"{getattr(s, 'title', '')} {getattr(s, 'selftext', '')}",
                    "source": f"reddit:{sub}",
                })
        return posts
    except Exception:
        return []

# -------- Twitter (X) API v2 via Bearer --------

_DEF_TW_QUERY = "({} OR ${}) (stock OR shares OR ETF) -is:retweet lang:en"

def _fetch_twitter(symbol: str, limit: int = 5) -> list[dict]:
    bearer = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer:
        return []
    try:
        url = "https://api.twitter.com/2/tweets/search/recent"
        query = _DEF_TW_QUERY.format(symbol, symbol)
        params = {
            "query": query,
            "max_results": min(max(limit, 10), 100),
            "tweet.fields": "created_at,lang",
        }
        headers = {"Authorization": f"Bearer {bearer}"}
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", [])
        out: list[dict] = []
        for t in data:
            out.append({
                "symbol": symbol,
                "timestamp": pd.to_datetime(t.get("created_at", datetime.utcnow()), utc=True),
                "text": t.get("text", ""),
                "source": "twitter",
            })
        return out
    except Exception:
        return []

# -------- NewsAPI (via REST) --------

def _fetch_news(symbol: str, limit: int = 5) -> list[dict]:
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        return []
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": symbol,
            "language": "en",
            "pageSize": limit,
            "sortBy": "publishedAt",
            "apiKey": key,
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        arts = r.json().get("articles", [])
        out: list[dict] = []
        for a in arts:
            out.append({
                "symbol": symbol,
                "timestamp": pd.to_datetime(a.get("publishedAt", datetime.utcnow()), utc=True),
                "text": f"{a.get('title','')} {a.get('description','')}",
                "source": f"news:{a.get('source',{}).get('name','news')}",
            })
        return out
    except Exception:
        return []

# -------- Alpha Vantage company news (optional) --------

def _fetch_alpha_news(symbol: str, limit: int = 10) -> list[dict]:
    key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not key:
        return []
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "sort": "LATEST",
            "limit": str(limit),
            "apikey": key,
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        js = r.json()
        feed = js.get("feed", [])
        out: list[dict] = []
        for item in feed:
            out.append({
                "symbol": symbol,
                "timestamp": pd.to_datetime(item.get("time_published"), format="%Y%m%dT%H%M%S" , utc=True, errors='coerce'),
                "text": f"{item.get('title','')} {item.get('summary','')}",
                "source": f"alpha_news:{item.get('source','alpha')}",
            })
        return out
    except Exception:
        return []

# -------- Aggregator --------

def collect_all_data(symbols: List[str], reddit_limit: int = 5, news_limit: int = 5, twitter_limit: int = 5) -> pd.DataFrame:
    rows: list[dict] = []
    for s in symbols:
        rows.extend(_fetch_reddit(s, reddit_limit))
        rows.extend(_fetch_twitter(s, twitter_limit))
        rows.extend(_fetch_news(s, news_limit))
        rows.extend(_fetch_alpha_news(s, news_limit))
        # Fallback if nothing fetched
        if not any(r.get("symbol") == s for r in rows):
            rows.append({
                "symbol": s,
                "timestamp": pd.Timestamp.utcnow(),
                "text": f"No live data fetched for {s}",
                "source": "placeholder",
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        # Normalize schema
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["text"] = df["text"].astype(str)
        df["source"] = df["source"].astype(str)
    return df
