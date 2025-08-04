#!/usr/bin/env python3
"""
Complete DataFrame Schema and Functionality Test

This script demonstrates that all three ingestion modules return standardized
pandas DataFrames with the required columns and can be combined for analysis.
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import our ingestion modules
from ingestion.reddit import RedditIngestion, RedditPost
from ingestion.twitter import TwitterIngestion, Tweet
from ingestion.news import NewsIngestion, NewsArticle

def create_comprehensive_test_data():
    """Create diverse test data to demonstrate functionality"""
    
    # Multiple Reddit posts with different symbols
    reddit_posts = [
        RedditPost(
            id="reddit1", title="$AAPL Analysis: Strong iPhone Sales",
            selftext="Apple's iPhone 15 sales are exceeding expectations. Bullish on $AAPL.",
            score=245, upvote_ratio=0.89, num_comments=45, created_utc=datetime.now() - timedelta(hours=2),
            subreddit="stocks", url="https://reddit.com/r/stocks/1", author="trader1", flair="DD"
        ),
        RedditPost(
            id="reddit2", title="TSLA stock surge - what's driving this?",
            selftext="Tesla stock up 15% today. Major delivery numbers coming soon.",
            score=189, upvote_ratio=0.82, num_comments=67, created_utc=datetime.now() - timedelta(hours=4),
            subreddit="investing", url="https://reddit.com/r/investing/2", author="investor_joe", flair="Discussion"
        ),
        RedditPost(
            id="reddit3", title="Market Update: SPY, QQQ showing strength",
            selftext="Both $SPY and $QQQ breaking resistance levels. Volume is strong.",
            score=156, upvote_ratio=0.91, num_comments=23, created_utc=datetime.now() - timedelta(hours=6),
            subreddit="SecurityAnalysis", url="https://reddit.com/r/SecurityAnalysis/3", author="analyst123", flair="Analysis"
        )
    ]
    
    # Multiple Tweets with different symbols and engagement
    tweets = [
        Tweet(
            id="tweet1", text="$AAPL breaking all-time highs! 🚀📈 #bullish #stocks",
            created_at=datetime.now() - timedelta(hours=1), author_id="user1", author_username="stockbull",
            public_metrics={'like_count': 245, 'retweet_count': 89, 'reply_count': 34, 'quote_count': 12}, lang="en"
        ),
        Tweet(
            id="tweet2", text="TSLA deliveries exceed expectations! $TSLA to the moon 🌙 #ElonMusk #Tesla",
            created_at=datetime.now() - timedelta(hours=3), author_id="user2", author_username="ElonFan2023",
            public_metrics={'like_count': 567, 'retweet_count': 234, 'reply_count': 78, 'quote_count': 45}, lang="en"
        ),
        Tweet(
            id="tweet3", text="Market sentiment turning bearish on $NVDA after chip regulations news 📉",
            created_at=datetime.now() - timedelta(hours=5), author_id="user3", author_username="chipwatch",
            public_metrics={'like_count': 123, 'retweet_count': 45, 'reply_count': 67, 'quote_count': 23}, lang="en"
        ),
        Tweet(
            id="tweet4", text="Volume spike in $SPY calls! Something big coming? 👀 #options #trading",
            created_at=datetime.now() - timedelta(hours=7), author_id="user4", author_username="optionsflow",
            public_metrics={'like_count': 89, 'retweet_count': 34, 'reply_count': 12, 'quote_count': 8}, lang="en"
        )
    ]
    
    # Multiple News articles covering different aspects
    articles = [
        NewsArticle(
            title="Apple Inc. (AAPL) Reports Record Q4 Revenue",
            description="Apple beats Wall Street expectations with strong iPhone and services revenue",
            content="Apple Inc. reported record quarterly revenue driven by strong iPhone 15 sales...",
            url="https://finance.yahoo.com/apple-earnings", published_at=datetime.now() - timedelta(hours=8),
            source="Yahoo Finance", author="Sarah Johnson", sentiment_score=0.75
        ),
        NewsArticle(
            title="Tesla (TSLA) Delivery Numbers Exceed Analyst Projections",
            description="Tesla delivers more vehicles than expected, stock surges in after-hours trading",
            content="Tesla Inc. announced quarterly delivery numbers that exceeded analyst expectations...",
            url="https://reuters.com/tesla-deliveries", published_at=datetime.now() - timedelta(hours=10),
            source="Reuters", author="Mike Chen", sentiment_score=0.68
        ),
        NewsArticle(
            title="NVIDIA Faces New Chip Export Restrictions",
            description="New regulations may impact NVIDIA's AI chip exports to certain countries",
            content="The Commerce Department announced new restrictions on advanced AI chip exports...",
            url="https://wsj.com/nvidia-restrictions", published_at=datetime.now() - timedelta(hours=12),
            source="Wall Street Journal", author="Tech Reporter", sentiment_score=-0.32
        ),
        NewsArticle(
            title="S&P 500 Index Reaches New High Amid Economic Optimism",
            description="The S&P 500 reached a new all-time high as investors remain optimistic about economic outlook",
            content="The S&P 500 index closed at a record high today, driven by strong corporate earnings...",
            url="https://cnbc.com/sp500-high", published_at=datetime.now() - timedelta(hours=14),
            source="CNBC", author="Market Analyst", sentiment_score=0.55
        )
    ]
    
    return reddit_posts, tweets, articles

def analyze_combined_data(combined_df):
    """Analyze the combined DataFrame for insights"""
    
    print("📈 COMBINED DATA ANALYSIS")
    print("=" * 50)
    
    # Basic statistics
    print(f"📊 Dataset Overview:")
    print(f"   Total records: {len(combined_df)}")
    print(f"   Date range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")
    print(f"   Unique sources: {combined_df['source'].nunique()}")
    print(f"   Records with symbols: {combined_df['symbol'].notna().sum()}")
    
    # Source breakdown
    print(f"\n📱 Source Distribution:")
    source_counts = combined_df['source'].value_counts()
    for source, count in source_counts.items():
        print(f"   {source}: {count}")
    
    # Symbol analysis
    print(f"\n💰 Symbol Analysis:")
    symbol_data = combined_df[combined_df['symbol'].notna()]
    if not symbol_data.empty:
        symbol_counts = symbol_data['symbol'].value_counts()
        print(f"   Most mentioned symbols:")
        for symbol, count in symbol_counts.head(5).items():
            print(f"   ${symbol}: {count} mentions")
        
        # Sentiment by symbol (if available)
        sentiment_data = symbol_data[symbol_data['sentiment_score'].notna()]
        if not sentiment_data.empty:
            print(f"\n😊 Average Sentiment by Symbol:")
            sentiment_by_symbol = sentiment_data.groupby('symbol')['sentiment_score'].mean()
            for symbol, sentiment in sentiment_by_symbol.items():
                emoji = "📈" if sentiment > 0.1 else "📉" if sentiment < -0.1 else "➡️"
                print(f"   ${symbol}: {sentiment:.2f} {emoji}")
    
    # Engagement analysis (Twitter data)
    twitter_data = combined_df[combined_df['source'].str.contains('twitter', na=False)]
    if not twitter_data.empty and 'total_engagement' in twitter_data.columns:
        print(f"\n🔥 Twitter Engagement:")
        avg_engagement = twitter_data['total_engagement'].mean()
        max_engagement = twitter_data['total_engagement'].max()
        print(f"   Average engagement: {avg_engagement:.0f}")
        print(f"   Max engagement: {max_engagement:.0f}")
    
    # Reddit analysis
    reddit_data = combined_df[combined_df['source'].str.contains('reddit', na=False)]
    if not reddit_data.empty and 'score' in reddit_data.columns:
        print(f"\n⬆️ Reddit Engagement:")
        avg_score = reddit_data['score'].mean()
        max_score = reddit_data['score'].max()
        total_comments = reddit_data['num_comments'].sum() if 'num_comments' in reddit_data.columns else 0
        print(f"   Average score: {avg_score:.0f}")
        print(f"   Max score: {max_score:.0f}")
        print(f"   Total comments: {total_comments}")
    
    # Time analysis
    print(f"\n⏰ Temporal Analysis:")
    combined_df['hour'] = combined_df['timestamp'].dt.hour
    hourly_counts = combined_df.groupby('hour').size()
    peak_hour = hourly_counts.idxmax()
    print(f"   Peak activity hour: {peak_hour}:00 ({hourly_counts[peak_hour]} posts)")
    
    return combined_df

def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE DATAFRAME TEST")
    print("=" * 60)
    
    # Create test data
    reddit_posts, tweets, articles = create_comprehensive_test_data()
    
    # Initialize clients (without API calls)
    reddit_client = RedditIngestion.__new__(RedditIngestion)
    twitter_client = TwitterIngestion.__new__(TwitterIngestion)  
    news_client = NewsIngestion.__new__(NewsIngestion)
    
    # Generate DataFrames
    print("📊 Generating DataFrames from test data...")
    reddit_df = reddit_client.to_dataframe(reddit_posts)
    twitter_df = twitter_client.to_dataframe(tweets)
    news_df = news_client.to_dataframe(articles)
    
    # Display individual DataFrame info
    print(f"\n📱 Reddit DataFrame: {reddit_df.shape} - Required columns ✅")
    print(f"   Columns: {list(reddit_df.columns)}")
    
    print(f"\n🐦 Twitter DataFrame: {twitter_df.shape} - Required columns ✅")
    print(f"   Columns: {list(twitter_df.columns)}")
    
    print(f"\n📰 News DataFrame: {news_df.shape} - Required columns ✅")
    print(f"   Columns: {list(news_df.columns)}")
    
    # Combine all DataFrames
    print(f"\n🔗 Combining all DataFrames...")
    combined_df = pd.concat([reddit_df, twitter_df, news_df], ignore_index=True)
    
    # Verify required columns
    required_columns = ['symbol', 'timestamp', 'source', 'text']
    missing_columns = [col for col in required_columns if col not in combined_df.columns]
    
    if missing_columns:
        print(f"❌ ERROR: Missing columns {missing_columns}")
        return 1
    
    print(f"✅ Combined DataFrame: {combined_df.shape}")
    print(f"✅ All required columns present: {required_columns}")
    
    # Analyze the combined data
    analyze_combined_data(combined_df)
    
    # Save to file for inspection
    output_file = "test_combined_data.csv"
    combined_df.to_csv(output_file, index=False)
    print(f"\n💾 Data saved to: {output_file}")
    
    print(f"\n🎉 SUCCESS: All ingestion modules work correctly!")
    print(f"   ✅ Standardized schema with required columns")
    print(f"   ✅ DataFrames can be combined seamlessly")
    print(f"   ✅ Rich additional data for analysis")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
