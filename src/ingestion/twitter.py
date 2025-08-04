"""
Twitter Data Ingestion Module

This module provides functionality to fetch Twitter data using the Tweepy library.
Includes rate limiting management and sentiment-focused data collection.
"""

import tweepy
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import time
import logging
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Data class for Tweet information"""
    id: str
    text: str
    created_at: datetime
    author_id: str
    author_username: str
    public_metrics: Dict[str, int]  # retweet_count, like_count, reply_count, quote_count
    lang: str
    context_annotations: Optional[List[Dict]] = None
    referenced_tweets: Optional[List[Dict]] = None
    entities: Optional[Dict] = None


class TwitterIngestion:
    """
    Twitter data ingestion class for fetching tweets related to trading and finance.
    Uses Twitter API v2 with Tweepy.
    """
    
    def __init__(self):
        """
        Initialize Twitter API client with credentials from environment variables.
        
        Required environment variables:
        - TWITTER_BEARER_TOKEN (for API v2)
        - TWITTER_API_KEY (optional, for API v1.1 features)
        - TWITTER_API_SECRET (optional)
        - TWITTER_ACCESS_TOKEN (optional)
        - TWITTER_ACCESS_TOKEN_SECRET (optional)
        """
        self.client = self._initialize_twitter()
        
        # Financial Twitter accounts to monitor
        self.financial_accounts = [
            'DeItaone',  # Breaking news
            'unusual_whales',  # Options flow
            'zerohedge',  # Financial news
            'YahooFinance',  # Yahoo Finance
            'MarketWatch',  # Market Watch
            'CNBC',  # CNBC
            'BloombergTV',  # Bloomberg
            'Reuters',  # Reuters Business
            'WSJ',  # Wall Street Journal
            'FT',  # Financial Times
            'Benzinga',  # Benzinga
            'SeekingAlpha',  # Seeking Alpha
            'TradingView',  # TradingView
            'FinancialTimes'  # Financial Times
        ]
        
        # Financial keywords and hashtags
        self.financial_keywords = [
            'stocks', 'trading', 'investing', 'NYSE', 'NASDAQ',
            'SPY', 'QQQ', 'earnings', 'options', 'futures',
            'bullish', 'bearish', 'breakout', 'support', 'resistance'
        ]
        
        # Tweet fields to retrieve
        self.tweet_fields = [
            'id', 'text', 'created_at', 'author_id', 'public_metrics',
            'lang', 'context_annotations', 'referenced_tweets', 'entities'
        ]
        
        # User fields to retrieve
        self.user_fields = [
            'id', 'username', 'name', 'verified', 'public_metrics'
        ]
    
    def _initialize_twitter(self) -> tweepy.Client:
        """Initialize Twitter API v2 client"""
        try:
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if not bearer_token:
                raise ValueError("TWITTER_BEARER_TOKEN environment variable not set")
            
            client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                wait_on_rate_limit=False  # Don't wait, just return what we can get
            )
            
            logger.info("Twitter API v2 connection established successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize Twitter API: {e}")
            logger.info("Please set TWITTER_BEARER_TOKEN environment variable")
            raise
    
    def search_tweets(
        self,
        query: str,
        max_results: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Tweet]:
        """
        Search for tweets using Twitter API v2.
        
        Args:
            query: Search query (supports Twitter search operators)
            max_results: Maximum number of tweets to retrieve (10-100 for recent, 10-500 for full archive)
            start_time: Start time for search (within last 7 days for recent search)
            end_time: End time for search
            
        Returns:
            List of Tweet objects
        """
        try:
            # Default to last 24 hours if no start_time provided
            if start_time is None:
                start_time = datetime.now() - timedelta(hours=24)
            
            # Limit max_results to avoid rate limiting
            max_results = min(max_results, 50)  # Reduced from 100
            
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                start_time=start_time,
                end_time=end_time,
                tweet_fields=['id', 'text', 'created_at', 'author_id', 'public_metrics', 'lang'],
                user_fields=['id', 'username'],
                expansions=['author_id']
            )
            
            tweets = []
            if response.data:
                # Create username mapping from includes
                users = {}
                if response.includes and 'users' in response.includes:
                    users = {user.id: user.username for user in response.includes['users']}
                
                for tweet_data in response.data:
                    tweet = Tweet(
                        id=tweet_data.id,
                        text=tweet_data.text,
                        created_at=tweet_data.created_at,
                        author_id=tweet_data.author_id,
                        author_username=users.get(tweet_data.author_id, 'unknown'),
                        public_metrics=tweet_data.public_metrics or {},
                        lang=tweet_data.lang or 'unknown',
                        context_annotations=getattr(tweet_data, 'context_annotations', None),
                        referenced_tweets=getattr(tweet_data, 'referenced_tweets', None),
                        entities=getattr(tweet_data, 'entities', None)
                    )
                    tweets.append(tweet)
            
            logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            if "rate limit" in str(e).lower():
                logger.warning("Rate limit hit - try again later or reduce request frequency")
            return []
    
    def search_stock_tweets(
        self,
        symbol: str,
        max_results: int = 100,
        include_retweets: bool = False
    ) -> List[Tweet]:
        """
        Search for tweets mentioning a specific stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            max_results: Maximum number of tweets
            include_retweets: Whether to include retweets
            
        Returns:
            List of Tweet objects
        """
        # Build simpler search query for free tier
        query_parts = [symbol]  # Just use the symbol directly
        
        if not include_retweets:
            query_parts.append("-is:retweet")
        
        # Add language filter for English
        query_parts.append("lang:en")
        
        # Simple query without advanced operators
        query = f"{symbol} {' '.join(query_parts[1:])}"
        
        return self.search_tweets(query, max_results)
    
    def get_financial_timeline(
        self,
        usernames: List[str] = None,
        max_results: int = 50
    ) -> List[Tweet]:
        """
        Get recent tweets from financial Twitter accounts.
        This is often more reliable than search due to lower rate limits.
        
        Args:
            usernames: List of Twitter usernames (defaults to financial_accounts)
            max_results: Maximum tweets per user
            
        Returns:
            List of Tweet objects
        """
        if usernames is None:
            # Use a smaller subset for faster results
            usernames = ['YahooFinance', 'MarketWatch', 'CNBC'][:2]  # Limit to 2 accounts
        
        all_tweets = []
        
        for username in usernames:
            try:
                # Get user ID first
                user = self.client.get_user(username=username)
                if not user.data:
                    logger.warning(f"User not found: {username}")
                    continue
                
                # Get user's recent tweets with minimal fields
                response = self.client.get_users_tweets(
                    id=user.data.id,
                    max_results=min(max_results, 10),  # Keep it small
                    tweet_fields=['id', 'text', 'created_at', 'public_metrics'],
                    exclude=['retweets', 'replies']  # Only original tweets
                )
                
                if response.data:
                    for tweet_data in response.data:
                        tweet = Tweet(
                            id=tweet_data.id,
                            text=tweet_data.text,
                            created_at=tweet_data.created_at,
                            author_id=tweet_data.author_id,
                            author_username=username,
                            public_metrics=tweet_data.public_metrics or {},
                            lang='en',  # Assume English for financial accounts
                            context_annotations=None,
                            referenced_tweets=None,
                            entities=None
                        )
                        all_tweets.append(tweet)
                
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error fetching tweets from @{username}: {e}")
                continue
        
        # Sort by creation time (newest first)
        all_tweets.sort(key=lambda x: x.created_at, reverse=True)
        logger.info(f"Fetched {len(all_tweets)} tweets from financial accounts")
        
        return all_tweets
    
    def search_trending_stocks(
        self,
        trending_hashtags: List[str] = None,
        max_results: int = 100
    ) -> Dict[str, List[Tweet]]:
        """
        Search for tweets about trending stocks and financial topics.
        
        Args:
            trending_hashtags: List of hashtags to search
            max_results: Maximum tweets per hashtag
            
        Returns:
            Dictionary mapping hashtags to lists of tweets
        """
        if trending_hashtags is None:
            trending_hashtags = [
                '#stocks', '#trading', '#investing', '#earnings',
                '#breakout', '#bullish', '#bearish', '#SPY',
                '#nasdaq', '#wallstreet', '#fintech'
            ]
        
        results = {}
        
        for hashtag in trending_hashtags:
            query = f"{hashtag} lang:en -is:retweet"
            tweets = self.search_tweets(query, max_results)
            results[hashtag] = tweets
            
            # Small delay to respect rate limits
            time.sleep(1)
        
        total_tweets = sum(len(tweets) for tweets in results.values())
        logger.info(f"Found {total_tweets} tweets across {len(trending_hashtags)} hashtags")
        
        return results
    
    def extract_stock_symbols(self, text: str) -> List[str]:
        """
        Extract stock symbols from tweet text.
        
        Args:
            text: Tweet text
            
        Returns:
            List of stock symbols found
        """
        import re
        
        # Find patterns like $AAPL or $TSLA
        cashtag_pattern = r'\$([A-Z]{1,5})\b'
        symbols = re.findall(cashtag_pattern, text.upper())
        
        return list(set(symbols))  # Remove duplicates
    
    def get_tweet_sentiment_indicators(self, tweets: List[Tweet]) -> Dict[str, Any]:
        """
        Analyze tweets for basic sentiment indicators.
        
        Args:
            tweets: List of Tweet objects
            
        Returns:
            Dictionary with sentiment metrics
        """
        if not tweets:
            return {}
        
        total_tweets = len(tweets)
        total_likes = sum(tweet.public_metrics.get('like_count', 0) for tweet in tweets)
        total_retweets = sum(tweet.public_metrics.get('retweet_count', 0) for tweet in tweets)
        total_replies = sum(tweet.public_metrics.get('reply_count', 0) for tweet in tweets)
        
        # Count bullish/bearish keywords
        bullish_keywords = ['bullish', 'bull', 'buy', 'long', 'call', 'moon', 'rocket', '🚀', '📈']
        bearish_keywords = ['bearish', 'bear', 'sell', 'short', 'put', 'crash', 'dump', '📉']
        
        bullish_count = 0
        bearish_count = 0
        
        for tweet in tweets:
            text_lower = tweet.text.lower()
            if any(keyword in text_lower for keyword in bullish_keywords):
                bullish_count += 1
            if any(keyword in text_lower for keyword in bearish_keywords):
                bearish_count += 1
        
        return {
            'total_tweets': total_tweets,
            'total_engagement': total_likes + total_retweets + total_replies,
            'avg_likes': total_likes / total_tweets if total_tweets > 0 else 0,
            'avg_retweets': total_retweets / total_tweets if total_tweets > 0 else 0,
            'bullish_mentions': bullish_count,
            'bearish_mentions': bearish_count,
            'bullish_ratio': bullish_count / total_tweets if total_tweets > 0 else 0,
            'bearish_ratio': bearish_count / total_tweets if total_tweets > 0 else 0
        }
    
    def to_dataframe(self, tweets: List[Tweet]) -> pd.DataFrame:
        """
        Convert list of Tweet objects to pandas DataFrame.
        
        Args:
            tweets: List of Tweet objects
            
        Returns:
            pandas DataFrame with standardized columns: ['symbol', 'timestamp', 'source', 'text', ...]
        """
        if not tweets:
            return pd.DataFrame()
        
        data = []
        for tweet in tweets:
            # Extract stock symbols from text
            symbols = self.extract_stock_symbols(tweet.text)
            symbol = symbols[0] if symbols else None  # Primary symbol
            
            data.append({
                'symbol': symbol,
                'timestamp': tweet.created_at,
                'source': f"twitter_{tweet.author_username}",
                'text': tweet.text,
                'id': tweet.id,
                'created_at': tweet.created_at,
                'author_id': tweet.author_id,
                'author_username': tweet.author_username,
                'like_count': tweet.public_metrics.get('like_count', 0),
                'retweet_count': tweet.public_metrics.get('retweet_count', 0),
                'reply_count': tweet.public_metrics.get('reply_count', 0),
                'quote_count': tweet.public_metrics.get('quote_count', 0),
                'lang': tweet.lang,
                'all_symbols': symbols,
                'symbol_count': len(symbols),
                'total_engagement': (
                    tweet.public_metrics.get('like_count', 0) +
                    tweet.public_metrics.get('retweet_count', 0) +
                    tweet.public_metrics.get('reply_count', 0) +
                    tweet.public_metrics.get('quote_count', 0)
                )
            })
        
        return pd.DataFrame(data)


# Example usage and testing
if __name__ == "__main__":
    # Initialize Twitter ingestion
    twitter_client = TwitterIngestion()
    
    # Example: Search for AAPL tweets
    aapl_tweets = twitter_client.search_stock_tweets('AAPL', max_results=20)
    print(f"Found {len(aapl_tweets)} tweets about AAPL")
    
    # Convert to DataFrame
    df = twitter_client.to_dataframe(aapl_tweets)
    if not df.empty:
        print(f"\nTweet metrics:")
        print(f"Average likes: {df['like_count'].mean():.1f}")
        print(f"Average retweets: {df['retweet_count'].mean():.1f}")
        print(f"Total engagement: {df[['like_count', 'retweet_count', 'reply_count']].sum().sum()}")
    
    # Example: Get sentiment indicators
    sentiment = twitter_client.get_tweet_sentiment_indicators(aapl_tweets)
    print(f"\nSentiment analysis: {sentiment}")
    
    # Example: Get financial timeline
    financial_tweets = twitter_client.get_financial_timeline(
        usernames=['YahooFinance', 'MarketWatch'], 
        max_results=10
    )
    print(f"\nFound {len(financial_tweets)} tweets from financial accounts")
