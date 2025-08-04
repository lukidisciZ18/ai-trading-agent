#!/usr/bin/env python3
"""
Fast Twitter API Test - Optimized for Rate Limits
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

print("\n🚀 OPTIMIZED TWITTER TEST")
print("=" * 40)

# Test Twitter with optimized approach
try:
    print("🐦 Testing Twitter API (Rate-limit optimized)...")
    from ingestion.twitter import TwitterIngestion
    twitter = TwitterIngestion()
    
    # Method 1: Try financial timeline (usually faster)
    print("   📈 Method 1: Financial account timeline...")
    tweets = twitter.get_financial_timeline(max_results=5)
    
    if tweets:
        print(f"   ✅ Success: Got {len(tweets)} tweets from financial accounts")
        print(f"   📝 Sample: '{tweets[0].text[:60]}...'")
        print(f"   👤 From: @{tweets[0].author_username}")
        
        # Test DataFrame
        df = twitter.to_dataframe(tweets)
        print(f"   📊 DataFrame: {df.shape}")
        symbols = df[df['symbol'].notna()]['symbol'].unique()
        if len(symbols) > 0:
            print(f"   💰 Symbols: {list(symbols)}")
    else:
        print("   ⚠️ No tweets from financial timeline")
        
        # Method 2: Try simple search as fallback
        print("   🔍 Method 2: Simple search fallback...")
        tweets = twitter.search_tweets("AAPL", max_results=10)
        
        if tweets:
            print(f"   ✅ Search success: Got {len(tweets)} tweets")
            df = twitter.to_dataframe(tweets)
            print(f"   📊 DataFrame: {df.shape}")
        else:
            print("   ❌ Search also failed - likely rate limited")
            print("   💡 Suggestion: Wait 15 minutes and try again")
            
except Exception as e:
    print(f"❌ Twitter error: {e}")
    
    if "rate limit" in str(e).lower():
        print("💡 Rate limit solutions:")
        print("   1. Wait 15 minutes before next request")
        print("   2. Use smaller max_results (5-10)")
        print("   3. Focus on Reddit and News APIs instead")
        print("   4. Consider Twitter premium API for higher limits")

print("\n" + "=" * 40)
print("📋 TWITTER API OPTIMIZATION SUMMARY:")
print("✅ Reduced request sizes (5-10 tweets max)")
print("✅ Disabled wait_on_rate_limit for faster fails")
print("✅ Simplified search queries")
print("✅ Financial timeline as primary method")
print("💡 For production: Consider caching and scheduled runs")
