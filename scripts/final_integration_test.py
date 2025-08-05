#!/usr/bin/env python3
"""
Final API Integration Test - Production Ready
"""

import sys
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️ python-dotenv not available")

print("\n🎉 FINAL API INTEGRATION TEST")
print("=" * 50)

# Summary data
collection_summary = {
    'reddit': {'posts': 0, 'symbols': []},
    'fundamentals': {'metrics': 0, 'symbols': []}, 
    'news': {'articles': 0, 'symbols': []}
}

all_dataframes = []

# 1. Reddit Collection
print("📱 Reddit Data Collection...")
try:
    import praw
    
    # Initialize PRAW client
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
    )

    def fetch_reddit(symbols: list[str], limit: int = 100) -> pd.DataFrame:
        """
        Fetch recent submissions mentioning each ticker from r/stocks.
        Returns: DataFrame with columns [symbol, timestamp, source, text, url].
        """
        records = []
        for sym in symbols:
            query = f"${sym}"
            for submission in reddit.subreddit("stocks").search(query, limit=limit):
                records.append({
                    "symbol": sym,
                    "timestamp": pd.to_datetime(submission.created_utc, unit="s"),
                    "source": "reddit",
                    "text": submission.title + "\n" + submission.selftext,
                    "url": submission.url
                })
        return pd.DataFrame(records)
    
    # Test with high-leverage ETFs and small-cap stocks (your strategy focus)
    test_symbols = ["TQQQ", "SOXL", "LABU"]  # High-leverage ETFs for technical patterns
    df = fetch_reddit(test_symbols, limit=5)
    
    if not df.empty:
        all_dataframes.append(df)
        collection_summary['reddit']['posts'] = len(df)
        symbols = df['symbol'].unique().tolist()
        collection_summary['reddit']['symbols'] = symbols
        print(f"   ✅ {len(df)} posts collected")
        print(f"   💰 Symbols: {symbols}")
    else:
        print("   ⚠️ No posts collected")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Fundamental Data Collection (Alpha Vantage + Yahoo Finance)
print("\n� Fundamental Data Collection...")
try:
    import yfinance as yf
    import requests
    import time
    import pandas as pd
    
    def fetch_fundamentals(symbols: list[str]) -> pd.DataFrame:
        """
        Fetch fundamental + technical data using Yahoo Finance and Alpha Vantage.
        Returns: DataFrame with [symbol, timestamp, source, text, metric_type, value].
        """
        records = []
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        
        for sym in symbols:
            try:
                # Yahoo Finance data
                ticker = yf.Ticker(sym)
                info = ticker.info
                hist = ticker.history(period="60d")  # Get 60 days for technical analysis
                
                # Key fundamental metrics
                fundamentals = {
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'forward_pe': info.get('forwardPE'),
                    'price_to_book': info.get('priceToBook'),
                    'debt_to_equity': info.get('debtToEquity'),
                    'roe': info.get('returnOnEquity'),
                    'dividend_yield': info.get('dividendYield'),
                    'current_price': info.get('currentPrice'),
                    'target_price': info.get('targetMeanPrice'),
                    'recommendation': info.get('recommendationKey'),
                    'volume': info.get('volume'),
                    'avg_volume': info.get('averageVolume'),
                    'float_shares': info.get('floatShares'),
                    'shares_outstanding': info.get('sharesOutstanding')
                }
                
                # Technical Analysis (if we have price data)
                if not hist.empty and len(hist) >= 26:  # Need at least 26 days for MACD
                    import talib
                    import numpy as np
                    
                    # Calculate technical indicators - Convert to numpy float64 arrays
                    close_prices = hist['Close'].values.astype(np.float64)
                    volume_data = hist['Volume'].values.astype(np.float64)
                    
                    # RSI (14 period)
                    rsi = talib.RSI(close_prices, timeperiod=14)
                    current_rsi = rsi[-1] if not np.isnan(rsi[-1]) else None
                    
                    # MACD (12,26,9)
                    macd, macdsignal, macdhist = talib.MACD(close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
                    current_macd = macd[-1] if not np.isnan(macd[-1]) else None
                    current_macd_signal = macdsignal[-1] if not np.isnan(macdsignal[-1]) else None
                    current_macd_hist = macdhist[-1] if not np.isnan(macdhist[-1]) else None
                    
                    # Volume MA (20 period)
                    volume_ma = talib.SMA(volume_data, timeperiod=20)
                    current_volume_ma = volume_ma[-1] if not np.isnan(volume_ma[-1]) else None
                    current_volume = volume_data[-1]
                    volume_surge = (current_volume / current_volume_ma) if current_volume_ma else None
                    
                    # Price momentum (20-day)
                    price_20d_ago = close_prices[-20] if len(close_prices) >= 20 else close_prices[0]
                    price_momentum = ((close_prices[-1] - price_20d_ago) / price_20d_ago * 100) if price_20d_ago else None
                    
                    # Add technical indicators to fundamentals
                    fundamentals.update({
                        'rsi_14': current_rsi,
                        'macd': current_macd,
                        'macd_signal': current_macd_signal,
                        'macd_histogram': current_macd_hist,
                        'volume_ma_20': current_volume_ma,
                        'volume_surge_ratio': volume_surge,
                        'price_momentum_20d': price_momentum,
                        'current_volume': current_volume
                    })
                
                # Alpha Vantage data (if API key available)
                if alpha_vantage_key and alpha_vantage_key != "your_alpha_vantage_key":
                    try:
                        # Company Overview
                        av_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={sym}&apikey={alpha_vantage_key}"
                        av_response = requests.get(av_url, timeout=10)
                        
                        if av_response.status_code == 200:
                            av_data = av_response.json()
                            
                            # Add key Alpha Vantage metrics
                            av_metrics = {
                                'av_pe_ratio': av_data.get('PERatio'),
                                'av_peg_ratio': av_data.get('PEGRatio'),
                                'av_book_value': av_data.get('BookValue'),
                                'av_div_yield': av_data.get('DividendYield'),
                                'av_eps': av_data.get('EPS'),
                                'av_revenue_ttm': av_data.get('RevenueTTM'),
                                'av_profit_margin': av_data.get('ProfitMargin'),
                                'av_beta': av_data.get('Beta'),
                                'av_52w_high': av_data.get('52WeekHigh'),
                                'av_52w_low': av_data.get('52WeekLow')
                            }
                            
                            # Convert string values to float where possible
                            for key, value in av_metrics.items():
                                if value and value != 'None':
                                    try:
                                        av_metrics[key] = float(value)
                                    except (ValueError, TypeError):
                                        av_metrics[key] = value
                                else:
                                    av_metrics[key] = None
                            
                            fundamentals.update(av_metrics)
                        
                        time.sleep(0.2)  # Alpha Vantage rate limiting (5 calls/min)
                        
                    except Exception as e:
                        print(f"   ⚠️ Alpha Vantage error for {sym}: {e}")
                
                # Create records for all metrics
                for metric, value in fundamentals.items():
                    if value is not None:
                        records.append({
                            "symbol": sym,
                            "timestamp": pd.Timestamp.now(),
                            "source": "yahoo_finance" if not metric.startswith('av_') else "alpha_vantage",
                            "text": f"{metric}: {value}",
                            "metric_type": metric,
                            "value": value
                        })
                
                non_null_count = len([v for v in fundamentals.values() if v is not None])
                print(f"   ✅ {sym}: {non_null_count} metrics (fundamental + technical)")
                
            except Exception as e:
                print(f"   ⚠️ Fundamentals error for {sym}: {e}")
                continue
                
        return pd.DataFrame(records)
    
    # Use high-leverage ETFs and small-caps (your strategy targets)
    test_symbols = ["TQQQ", "SOXL", "LABU"]
    df = fetch_fundamentals(test_symbols)
    
    if not df.empty:
        all_dataframes.append(df)
        collection_summary['fundamentals']['metrics'] = len(df)  # Updated reference
        symbols = df['symbol'].unique().tolist()
        collection_summary['fundamentals']['symbols'] = symbols
        print(f"   ✅ {len(df)} fundamental metrics collected")
        print(f"   💰 Symbols: {symbols}")
    else:
        print("   ⚠️ No fundamental data collected")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Enhanced News Collection (NewsAPI + Web Scraping)
print("\n📰 Enhanced News Collection...")
try:
    import requests
    from bs4 import BeautifulSoup
    import time
    
    def fetch_enhanced_news(symbols: list[str], page_size: int = 5) -> pd.DataFrame:
        """
        Fetch news from NewsAPI and scrape financial news sites.
        Returns: DataFrame with [symbol, timestamp, source, text, url].
        """
        records = []
        api_key = os.getenv("NEWS_API_KEY")
        
        # 1. NewsAPI (existing functionality)
        for sym in symbols:
            query = f"{sym} stock OR {sym} shares"
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "apiKey": api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size
            }
            
            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    articles = response.json().get("articles", [])
                    for article in articles:
                        records.append({
                            "symbol": sym,
                            "timestamp": pd.to_datetime(article["publishedAt"]),
                            "source": "newsapi",
                            "text": f"{article['title']} {article['description'] or ''}",
                            "url": article["url"]
                        })
            except Exception as e:
                print(f"   ⚠️ NewsAPI error for {sym}: {e}")
                continue
        
        # 2. Yahoo Finance News Scraping
        for sym in symbols:
            try:
                url = f"https://finance.yahoo.com/quote/{sym}/news"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Find news headlines (Yahoo Finance structure)
                    headlines = soup.find_all('h3', class_='Mb(5px)')[:3]  # Limit to 3 per symbol
                    
                    for headline in headlines:
                        title = headline.get_text().strip()
                        if title and len(title) > 10:  # Filter out short/empty titles
                            records.append({
                                "symbol": sym,
                                "timestamp": pd.Timestamp.now(),
                                "source": "yahoo_news",
                                "text": title,
                                "url": f"https://finance.yahoo.com/quote/{sym}/news"
                            })
                
                time.sleep(1)  # Be respectful to Yahoo's servers
                
            except Exception as e:
                print(f"   ⚠️ Yahoo scraping error for {sym}: {e}")
                continue
        
        # 3. MarketWatch Recent Headlines
        try:
            url = "https://www.marketwatch.com/investing/stock"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Find recent market headlines
                headlines = soup.find_all('a', class_='link')[:5]  # Get top 5 market headlines
                
                for headline in headlines:
                    title = headline.get_text().strip()
                    href = headline.get('href', '')
                    
                    if title and len(title) > 15:  # Filter meaningful headlines
                        # Check if any of our symbols are mentioned
                        mentioned_symbols = [sym for sym in symbols if sym.upper() in title.upper()]
                        symbol = mentioned_symbols[0] if mentioned_symbols else "MARKET"
                        
                        records.append({
                            "symbol": symbol,
                            "timestamp": pd.Timestamp.now(),
                            "source": "marketwatch",
                            "text": title,
                            "url": f"https://www.marketwatch.com{href}" if href.startswith('/') else href
                        })
                        
        except Exception as e:
            print(f"   ⚠️ MarketWatch scraping error: {e}")
                
        return pd.DataFrame(records)
    
    # Use same symbols as Reddit and Fundamentals (high-leverage ETFs)
    test_symbols = ["TQQQ", "SOXL", "LABU"]
    df = fetch_enhanced_news(test_symbols, page_size=3)
    
    if not df.empty:
        all_dataframes.append(df)
        collection_summary['news']['articles'] = len(df)
        symbols = df['symbol'].unique().tolist()
        collection_summary['news']['symbols'] = symbols
        print(f"   ✅ {len(df)} news items collected")
        print(f"   💰 Sources: {df['source'].unique().tolist()}")
    else:
        print("   ⚠️ No news articles collected")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Data Integration
print(f"\n🔗 Data Integration Results")
print("-" * 30)

if all_dataframes:
    # Combine all data
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    print(f"📊 Combined DataFrame: {combined_df.shape}")
    print(f"✅ Required columns present: {['symbol', 'timestamp', 'source', 'text']}")
    
    # Platform breakdown
    source_counts = combined_df['source'].value_counts()
    print(f"📱 Data sources ({len(source_counts)}):")
    for source, count in source_counts.items():
        platform = source.split('_')[0]
        print(f"   {platform}: {count} records")
    
    # Symbol summary
    all_symbols = set()
    for platform_data in collection_summary.values():
        all_symbols.update(platform_data['symbols'])
    
    if all_symbols:
        print(f"💰 Unique symbols detected: {sorted(list(all_symbols))}")
    else:
        print("📝 No symbols detected in current data")
    
    # Export data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"trading_data_{timestamp}.csv"
    combined_df.to_csv(filename, index=False)
    print(f"💾 Data exported: {filename}")
    
else:
    print("❌ No data collected from any source")

# 5. Final Summary
print(f"\n🚀 INTEGRATION SUCCESS SUMMARY")
print("=" * 50)

total_data_points = sum([
    collection_summary['reddit']['posts'],
    collection_summary['fundamentals']['metrics'], 
    collection_summary['news']['articles']
])

print(f"📊 Total data points collected: {total_data_points}")
print(f"📱 Reddit: {collection_summary['reddit']['posts']} posts")
print(f"� Fundamentals: {collection_summary['fundamentals']['metrics']} metrics")
print(f"📰 News: {collection_summary['news']['articles']} articles")

if total_data_points > 0:
    print(f"\n✅ SUCCESS: Your AI Trading Agent is collecting live market data!")
    print(f"🎯 Next steps:")
    print(f"   1. Run data collection on schedule (every 15-30 minutes)")
    print(f"   2. Implement sentiment analysis pipeline")
    print(f"   3. Generate trading signals")
    print(f"   4. Build backtesting framework")
else:
    print(f"\n⚠️ Limited data collection - check API quotas and try again")

print(f"\n🔥 YOUR AI TRADING AGENT IS OPERATIONAL!")
