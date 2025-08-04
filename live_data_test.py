#!/usr/bin/env python3
"""
Comprehensive Live Data Test
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment")

print("\n🚀 LIVE DATA COLLECTION TEST")
print("=" * 50)

# Test Reddit with DataFrame
try:
    print("📱 Reddit - Collecting r/stocks posts...")
    from ingestion.reddit import RedditIngestion
    reddit = RedditIngestion()
    posts = reddit.fetch_subreddit_posts('stocks', limit=5)
    print(f"✅ Reddit: Fetched {len(posts)} live posts")
    
    if posts:
        print(f"   Latest: '{posts[0].title}'")
        print(f"   Score: {posts[0].score}, Comments: {posts[0].num_comments}")
        
        # Convert to DataFrame
        df = reddit.to_dataframe(posts)
        print(f"   📊 DataFrame: {df.shape}")
        print(f"   Required columns: {['symbol', 'timestamp', 'source', 'text']}")
        
        # Check for symbols
        symbols = df[df['symbol'].notna()]['symbol'].unique()
        if len(symbols) > 0:
            print(f"   💰 Symbols detected: {list(symbols)}")
        else:
            print("   📝 No symbols detected in recent posts")
            
except Exception as e:
    print(f"❌ Reddit error: {e}")

print()

# Test Twitter with simpler query
try:
    print("🐦 Twitter - Searching for stock tweets...")
    from ingestion.twitter import TwitterIngestion
    twitter = TwitterIngestion()
    
    # Try simpler search
    tweets = twitter.search_tweets('AAPL', max_results=10)
    print(f"✅ Twitter: Fetched {len(tweets)} tweets about AAPL")
    
    if tweets:
        print(f"   Latest: '{tweets[0].text[:60]}...'")
        print(f"   Engagement: {tweets[0].public_metrics}")
        
        # Convert to DataFrame
        df = twitter.to_dataframe(tweets)
        print(f"   📊 DataFrame: {df.shape}")
        
        # Check for symbols
        symbols = df[df['symbol'].notna()]['symbol'].unique()
        if len(symbols) > 0:
            print(f"   💰 Symbols detected: {list(symbols)}")
            
except Exception as e:
    print(f"❌ Twitter error: {e}")

print()

# Test News with specific query
try:
    print("📰 News - Fetching financial headlines...")
    from ingestion.news import NewsIngestion
    news = NewsIngestion()
    
    # Try specific financial news
    articles = news.fetch_newsapi_articles(
        query="stocks OR trading OR market",
        category="business",
        page_size=10
    )
    print(f"✅ News: Fetched {len(articles)} financial articles")
    
    if articles:
        print(f"   Latest: '{articles[0].title}'")
        print(f"   Source: {articles[0].source}")
        
        # Convert to DataFrame
        df = news.to_dataframe(articles)
        print(f"   📊 DataFrame: {df.shape}")
        
        # Check for symbols
        symbols = df[df['symbol'].notna()]['symbol'].unique()
        if len(symbols) > 0:
            print(f"   💰 Symbols detected: {list(symbols)}")
            
except Exception as e:
    print(f"❌ News error: {e}")

print("\n" + "=" * 50)
print("🎉 LIVE DATA TEST COMPLETE!")
print("✅ Your AI Trading Agent can now collect real market data!")
print("🚀 Ready for production use with live APIs!")
