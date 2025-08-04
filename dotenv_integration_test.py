#!/usr/bin/env python3
"""
Complete Integration Test with Python-dotenv

This script tests all three ingestion modules (Reddit, Twitter, News) 
with python-dotenv environment variable loading.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Import ingestion modules
from ingestion.reddit import RedditIngestion
from ingestion.twitter import TwitterIngestion  
from ingestion.news import NewsIngestion

def test_environment_variables():
    """Test that all required environment variables are loaded"""
    print("=== Testing Environment Variables ===")
    
    required_vars = {
        'Reddit': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT'],
        'Twitter': ['TWITTER_BEARER_TOKEN'],
        'News': ['NEWS_API_KEY']
    }
    
    missing_vars = []
    
    for service, vars_list in required_vars.items():
        print(f"\n{service} Variables:")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                print(f"  ✅ {var}: {'*' * min(len(value), 10)}...")
            else:
                print(f"  ❌ {var}: Not set")
                missing_vars.append(f"{service}.{var}")
    
    if missing_vars:
        print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All environment variables are set!")
        return True

def test_reddit_ingestion():
    """Test Reddit data ingestion"""
    print("\n=== Testing Reddit Ingestion ===")
    
    try:
        reddit_client = RedditIngestion()
        print("✅ Reddit client initialized successfully")
        
        # Fetch a small number of posts
        posts = reddit_client.fetch_subreddit_posts('stocks', limit=5)
        print(f"✅ Fetched {len(posts)} posts from r/stocks")
        
        # Convert to DataFrame
        df = reddit_client.to_dataframe(posts)
        print(f"✅ DataFrame created with {len(df)} rows and {len(df.columns)} columns")
        
        # Check required columns
        required_columns = ['symbol', 'timestamp', 'source', 'text']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if not missing_columns:
            print("✅ All required columns present in DataFrame")
        else:
            print(f"❌ Missing columns: {missing_columns}")
            return False, None
        
        return True, df
        
    except Exception as e:
        print(f"❌ Reddit ingestion failed: {e}")
        return False, None

def test_twitter_ingestion():
    """Test Twitter data ingestion"""
    print("\n=== Testing Twitter Ingestion ===")
    
    try:
        twitter_client = TwitterIngestion()
        print("✅ Twitter client initialized successfully")
        
        # Search for a common financial term
        tweets = twitter_client.search_tweets(query="AAPL", max_results=5)
        print(f"✅ Fetched {len(tweets)} tweets about AAPL")
        
        # Convert to DataFrame
        df = twitter_client.to_dataframe(tweets)
        print(f"✅ DataFrame created with {len(df)} rows and {len(df.columns)} columns")
        
        # Check required columns
        required_columns = ['symbol', 'timestamp', 'source', 'text']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if not missing_columns:
            print("✅ All required columns present in DataFrame")
        else:
            print(f"❌ Missing columns: {missing_columns}")
            return False, None
        
        return True, df
        
    except Exception as e:
        print(f"❌ Twitter ingestion failed: {e}")
        return False, None

def test_news_ingestion():
    """Test News data ingestion"""
    print("\n=== Testing News Ingestion ===")
    
    try:
        news_client = NewsIngestion()
        print("✅ News client initialized successfully")
        
        # Fetch financial news
        articles = news_client.fetch_newsapi_articles(query="Apple stock", page_size=5)
        print(f"✅ Fetched {len(articles)} news articles")
        
        # Convert to DataFrame
        df = news_client.to_dataframe(articles)
        print(f"✅ DataFrame created with {len(df)} rows and {len(df.columns)} columns")
        
        # Check required columns
        required_columns = ['symbol', 'timestamp', 'source', 'text']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if not missing_columns:
            print("✅ All required columns present in DataFrame")
        else:
            print(f"❌ Missing columns: {missing_columns}")
            return False, None
        
        return True, df
        
    except Exception as e:
        print(f"❌ News ingestion failed: {e}")
        return False, None

def test_combined_data_collection():
    """Test collecting and combining data from all sources"""
    print("\n=== Testing Combined Data Collection ===")
    
    all_dataframes = []
    
    # Test each ingestion module
    reddit_success, reddit_df = test_reddit_ingestion()
    twitter_success, twitter_df = test_twitter_ingestion()
    news_success, news_df = test_news_ingestion()
    
    # Collect successful DataFrames
    if reddit_success and reddit_df is not None and not reddit_df.empty:
        all_dataframes.append(reddit_df)
        print(f"✅ Reddit data: {len(reddit_df)} records")
    
    if twitter_success and twitter_df is not None and not twitter_df.empty:
        all_dataframes.append(twitter_df)
        print(f"✅ Twitter data: {len(twitter_df)} records")
    
    if news_success and news_df is not None and not news_df.empty:
        all_dataframes.append(news_df)
        print(f"✅ News data: {len(news_df)} records")
    
    if all_dataframes:
        # Combine all DataFrames
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        print(f"✅ Combined DataFrame: {len(combined_df)} total records")
        
        # Save to CSV with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dotenv_integration_test_{timestamp}.csv"
        combined_df.to_csv(filename, index=False)
        print(f"✅ Data saved to {filename}")
        
        # Display sample data
        print(f"\nSample data (first 3 rows):")
        print(combined_df[['symbol', 'timestamp', 'source', 'text']].head(3).to_string())
        
        return True, combined_df
    else:
        print("❌ No data collected from any source")
        return False, None

def main():
    """Main test function"""
    print("🚀 Starting Complete Integration Test with Python-dotenv")
    print("=" * 60)
    
    # Test environment variables
    env_success = test_environment_variables()
    
    if not env_success:
        print("\n❌ Environment variable test failed. Please check your .env file.")
        return False
    
    # Test combined data collection
    success, combined_df = test_combined_data_collection()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Python-dotenv integration successful!")
        print(f"📊 Total records collected: {len(combined_df)}")
        
        # Show source breakdown
        source_counts = combined_df['source'].value_counts()
        print("\n📈 Data by source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count} records")
        
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
