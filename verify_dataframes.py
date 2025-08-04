#!/usr/bin/env python3
"""
DataFrame Schema Verification Script

This script verifies that all ingestion modules return pandas DataFrames
with the required standardized columns: ['symbol', 'timestamp', 'source', 'text', ...].
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import our ingestion modules
try:
    from ingestion.reddit import RedditIngestion, RedditPost
    from ingestion.twitter import TwitterIngestion, Tweet
    from ingestion.news import NewsIngestion, NewsArticle
    print("✅ Successfully imported all ingestion modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Note: This is expected if dependencies are not installed in current environment")
    print("The modules will work correctly when run in the Poetry environment")


def create_mock_data():
    """Create mock data for testing DataFrame schemas"""
    
    # Mock Reddit post
    mock_reddit_post = RedditPost(
        id="test123",
        title="AAPL stock discussion - bullish on Apple",
        selftext="I think $AAPL is going to moon after earnings. What do you think?",
        score=150,
        upvote_ratio=0.85,
        num_comments=25,
        created_utc=datetime.now(),
        subreddit="stocks",
        url="https://reddit.com/r/stocks/test123",
        author="trader123",
        flair="DD"
    )
    
    # Mock Twitter tweet
    mock_tweet = Tweet(
        id="twitter123",
        text="$TSLA breaking out! Strong volume on this move. #stocks #trading",
        created_at=datetime.now(),
        author_id="user123",
        author_username="stocktrader",
        public_metrics={'like_count': 50, 'retweet_count': 20, 'reply_count': 10, 'quote_count': 5},
        lang="en"
    )
    
    # Mock News article
    mock_article = NewsArticle(
        title="Apple Inc. (AAPL) Reports Strong Q4 Earnings",
        description="Apple beats expectations with revenue growth",
        content="Apple Inc reported strong quarterly results...",
        url="https://example.com/apple-earnings",
        published_at=datetime.now(),
        source="Financial News",
        author="Jane Reporter",
        sentiment_score=0.8
    )
    
    return mock_reddit_post, mock_tweet, mock_article


def verify_dataframe_schema(df: pd.DataFrame, module_name: str) -> bool:
    """
    Verify that DataFrame has required columns and proper structure.
    
    Args:
        df: DataFrame to verify
        module_name: Name of the module being tested
        
    Returns:
        True if schema is valid, False otherwise
    """
    required_columns = ['symbol', 'timestamp', 'source', 'text']
    
    print(f"\n📊 Verifying {module_name} DataFrame schema:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"   ❌ Missing required columns: {missing_columns}")
        return False
    
    print(f"   ✅ All required columns present: {required_columns}")
    
    # Check data types
    if not df.empty:
        print(f"   📋 Data types:")
        for col in required_columns:
            dtype = df[col].dtype
            print(f"      {col}: {dtype}")
            
            # Validate specific column types
            if col == 'timestamp':
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    print(f"   ⚠️  Warning: {col} should be datetime type, got {dtype}")
            elif col == 'text':
                if not pd.api.types.is_string_dtype(df[col]) and df[col].dtype != 'object':
                    print(f"   ⚠️  Warning: {col} should be string type, got {dtype}")
        
        # Show sample data
        print(f"   📄 Sample data:")
        for col in required_columns:
            sample_value = df[col].iloc[0]
            print(f"      {col}: {sample_value}")
    
    return True


def main():
    """Main verification function"""
    print("🔍 DataFrame Schema Verification")
    print("=" * 50)
    
    # Create mock data
    mock_reddit_post, mock_tweet, mock_article = create_mock_data()
    
    all_valid = True
    
    try:
        # Test Reddit ingestion - skip API initialization, just test DataFrame method
        print("\n1️⃣ Testing Reddit Ingestion:")
        reddit_client = RedditIngestion.__new__(RedditIngestion)  # Create without __init__
        reddit_df = reddit_client.to_dataframe([mock_reddit_post])
        valid_reddit = verify_dataframe_schema(reddit_df, "Reddit")
        all_valid &= valid_reddit
        
        # Test Twitter ingestion - skip API initialization, just test DataFrame method
        print("\n2️⃣ Testing Twitter Ingestion:")
        twitter_client = TwitterIngestion.__new__(TwitterIngestion)  # Create without __init__
        twitter_df = twitter_client.to_dataframe([mock_tweet])
        valid_twitter = verify_dataframe_schema(twitter_df, "Twitter")
        all_valid &= valid_twitter
        
        # Test News ingestion - skip API initialization, just test DataFrame method
        print("\n3️⃣ Testing News Ingestion:")
        news_client = NewsIngestion.__new__(NewsIngestion)  # Create without __init__
        news_df = news_client.to_dataframe([mock_article])
        valid_news = verify_dataframe_schema(news_df, "News")
        all_valid &= valid_news
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        all_valid = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 SUCCESS: All modules return DataFrames with required schema!")
        print("   Required columns: ['symbol', 'timestamp', 'source', 'text']")
        print("   ✅ Reddit ingestion - PASSED")
        print("   ✅ Twitter ingestion - PASSED") 
        print("   ✅ News ingestion - PASSED")
    else:
        print("❌ FAILED: Some modules have schema issues")
        return 1
    
    # Demonstrate combined DataFrame
    try:
        print("\n🔗 Testing Combined DataFrame:")
        combined_df = pd.concat([reddit_df, twitter_df, news_df], ignore_index=True)
        print(f"   Combined shape: {combined_df.shape}")
        print(f"   Sources: {combined_df['source'].unique()}")
        print(f"   Symbols found: {combined_df['symbol'].dropna().unique()}")
        print("   ✅ DataFrames can be successfully combined!")
        
    except Exception as e:
        print(f"   ❌ Error combining DataFrames: {e}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
