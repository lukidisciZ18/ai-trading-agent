# AI Trading Agent

REST API and CLI for two strategies:
- Option 2: Leveraged ETFs (TQQQ, SOXL, LABU) on technical patterns.
- Option 1: Momentum trading for small/micro-cap stocks with AI sentiment.

Features
- FastAPI endpoints: /health, /signals (GET/POST)
- Data ingestion: Reddit (PRAW), Twitter/X (v2 recent search), NewsAPI, Alpha Vantage news
- Price data: yfinance by default, optional Alpha Vantage OHLCV
- Technicals: pandas-ta if available, fallback MA crossover
- Dockerized, no native TA-Lib required

Quick start
1) Environment
Create .env using the below template (values are examples):

ALPHA_VANTAGE_API_KEY=34CPC2O136HB5UM5
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=ai-trading-agent/0.2
TWITTER_BEARER_TOKEN=your_bearer
NEWSAPI_KEY=your_newsapi

2) Build and run API (Docker)
- docker build -t trading-agent .
- docker run --rm -p 8000:8000 --env-file .env trading-agent
- Test: curl http://127.0.0.1:8000/health

3) Endpoints
- GET /signals?strategy=leveraged_etf
- GET /signals?strategy=momentum_smallcap&symbols=AAPL,PLTR
- POST /signals with JSON: {"strategy":"leveraged_etf","symbols":["TQQQ","SOXL","LABU"]}

Strategies
- Leveraged ETFs: Uses MA cross + short momentum; combines with TA/volume/sentiment into enhanced score.
- Small-cap momentum: Breakout and volume expansion; boosts by live sentiment; uses Alpha Vantage OHLCV when available.

Data ingestion
- Reddit via PRAW on subs: stocks, wallstreetbets, investing
- Twitter v2 recent search via bearer token
- NewsAPI Everything endpoint
- Alpha Vantage NEWS_SENTIMENT feed

Local development
- Python 3.12+
- pip install -r requirements.txt
- Run API: python src/main.py --mode api
- Run signals: python src/main.py --mode signals --strategy leveraged_etf

Tests
- pip install -r requirements.txt && pip install pytest
- pytest -q

Notes
- External APIs are best-effort; failures gracefully fallback to empty data.
- pandas-ta is optional; when missing, a simple MA crossover is used.
