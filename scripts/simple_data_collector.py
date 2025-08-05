#!/usr/bin/env python3
"""
Simplified Data Collection Module for AI Trading Agent

Clean, direct implementation using your streamlined functions.
"""

import os
import praw
import pandas as pd
from dotenv import load_dotenv
import tweepy
import requests
from datetime import datetime
from typing import List

load_dotenv()  # reads .env

# Initialize API clients
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
)

twitter_client = tweepy.Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))

def fetch_reddit(symbols: List[str], limit: int = 100) -> pd.DataFrame:
    """
    Fetch recent submissions mentioning each ticker from r/stocks.
    Returns: DataFrame with columns [symbol, timestamp, source, text, url].
    """
    records = []
    for sym in symbols:
        query = f"${sym}"
        try:
            for submission in reddit.subreddit("stocks").search(query, limit=limit):
                records.append({
                    "symbol": sym,
                    "timestamp": pd.to_datetime(submission.created_utc, unit="s"),
                    "source": "reddit",
                    "text": submission.title + "\n" + submission.selftext,
                    "url": submission.url
                })
        except Exception as e:
            print(f"Reddit error for {sym}: {e}")
            continue
    return pd.DataFrame(records)

def fetch_twitter(symbols: List[str], max_results: int = 10) -> pd.DataFrame:
    """
    Fetch recent tweets mentioning each ticker (e.g. "$AAPL").
    Returns: DataFrame with [symbol, timestamp, source, text, tweet_id].
    Note: Twitter API requires max_results between 10-100
    """
    records = []
    # Ensure max_results is within Twitter's limits
    max_results = max(10, min(100, max_results))
    
    for sym in symbols:
        query = f"${sym} -is:retweet lang:en"
        try:
            resp = twitter_client.search_recent_tweets(
                query=query, 
                max_results=max_results,
                tweet_fields=["created_at","text","id"]
            )
            if not resp.data:
                continue
            for tweet in resp.data:
                records.append({
                    "symbol": sym,
                    "timestamp": tweet.created_at,
                    "source": "twitter",
                    "text": tweet.text,
                    "tweet_id": tweet.id
                })
        except Exception as e:
            print(f"Twitter error for {sym}: {e}")
            continue
    return pd.DataFrame(records)

def fetch_news(symbols: List[str], page_size: int = 10) -> pd.DataFrame:
    """
    Fetch recent news articles mentioning stock symbols.
    Returns: DataFrame with [symbol, timestamp, source, text, url].
    """
    records = []
    api_key = os.getenv("NEWS_API_KEY")
    
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
                        "source": "news",
                        "text": f"{article['title']} {article['description'] or ''}",
                        "url": article["url"]
                    })
            else:
                print(f"News API error for {sym}: {response.status_code}")
        except Exception as e:
            print(f"News error for {sym}: {e}")
            continue
            
    return pd.DataFrame(records)

def collect_all_data(symbols: List[str], reddit_limit: int = 20, 
                    twitter_limit: int = 10, news_limit: int = 5) -> pd.DataFrame:
    """
    Collect data from all sources and combine into single DataFrame.
    
    Args:
        symbols: List of stock symbols to monitor
        reddit_limit: Number of Reddit posts per symbol
        twitter_limit: Number of tweets per symbol
        news_limit: Number of news articles per symbol
        
    Returns:
        Combined DataFrame with all data
    """
    print(f"🔍 Collecting data for symbols: {symbols}")
    
    all_data = []
    
    # Reddit
    print("📱 Fetching Reddit data...")
    reddit_df = fetch_reddit(symbols, limit=reddit_limit)
    if not reddit_df.empty:
        all_data.append(reddit_df)
        print(f"   ✅ {len(reddit_df)} Reddit posts")
    
    # Twitter
    print("🐦 Fetching Twitter data...")
    twitter_df = fetch_twitter(symbols, max_results=twitter_limit)
    if not twitter_df.empty:
        all_data.append(twitter_df)
        print(f"   ✅ {len(twitter_df)} tweets")
    
    # News
    print("📰 Fetching News data...")
    news_df = fetch_news(symbols, page_size=news_limit)
    if not news_df.empty:
        all_data.append(news_df)
        print(f"   ✅ {len(news_df)} news articles")
    
    # Combine all data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"\n📊 Total: {len(combined_df)} data points collected")
        return combined_df
    else:
        print("\n⚠️ No data collected from any source")
        return pd.DataFrame()

def save_data(df: pd.DataFrame, filename: str = None) -> str:
    """Save DataFrame to CSV with timestamp."""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"trading_data_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    print(f"💾 Data saved: {filename}")
    return filename

# Example usage
if __name__ == "__main__":
    # Define your watchlist
    WATCHLIST = ["AAPL", "MSFT", "TSLA", "NVDA", "GOOGL"]
    
    # Collect data
    data = collect_all_data(WATCHLIST, reddit_limit=10, twitter_limit=10, news_limit=3)
    
    if not data.empty:
        # Save data
        filename = save_data(data)
        
        # Show summary
        print(f"\n📈 Summary by source:")
        source_counts = data['source'].value_counts()
        for source, count in source_counts.items():
            print(f"   {source}: {count} records")
        
        print(f"\n💰 Symbols with data:")
        symbol_counts = data['symbol'].value_counts()
        for symbol, count in symbol_counts.items():
            print(f"   {symbol}: {count} mentions")
            
        print(f"\n🎯 Next: Analyze this data for trading signals!")
    else:
        print("❌ No data collected. Check API credentials and rate limits.")
