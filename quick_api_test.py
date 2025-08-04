#!/usr/bin/env python3
"""
Quick API Test Script
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

print("\n🔍 Testing API Connections...")
print("=" * 40)

# Test Reddit
try:
    print("📱 Testing Reddit...")
    from ingestion.reddit import RedditIngestion
    reddit = RedditIngestion()
    posts = reddit.fetch_subreddit_posts('stocks', limit=3)
    print(f"✅ Reddit: Fetched {len(posts)} posts")
    if posts:
        print(f"   Sample: '{posts[0].title[:50]}...'")
except Exception as e:
    print(f"❌ Reddit error: {e}")

print()

# Test Twitter  
try:
    print("🐦 Testing Twitter...")
    from ingestion.twitter import TwitterIngestion
    twitter = TwitterIngestion()
    tweets = twitter.search_stock_tweets('AAPL', max_results=10)
    print(f"✅ Twitter: Fetched {len(tweets)} tweets")
    if tweets:
        print(f"   Sample: '{tweets[0].text[:50]}...'")
except Exception as e:
    print(f"❌ Twitter error: {e}")

print()

# Test News
try:
    print("📰 Testing News...")
    from ingestion.news import NewsIngestion
    news = NewsIngestion()
    articles = news.fetch_market_news(max_articles=5)
    print(f"✅ News: Fetched {len(articles)} articles")
    if articles:
        print(f"   Sample: '{articles[0].title[:50]}...'")
except Exception as e:
    print(f"❌ News error: {e}")

print("\n🎉 API Test Complete!")
