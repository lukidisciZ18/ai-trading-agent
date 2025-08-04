"""
Reddit Data Ingestion Module

This module provides functionality to fetch Reddit posts and comments
using the PRAW (Python Reddit API Wrapper) library for sentiment analysis.
"""

import praw
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Data class for Reddit post information"""
    id: str
    title: str
    selftext: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: datetime
    subreddit: str
    url: str
    author: str
    flair: Optional[str] = None


@dataclass
class RedditComment:
    """Data class for Reddit comment information"""
    id: str
    body: str
    score: int
    created_utc: datetime
    author: str
    parent_id: str


class RedditIngestion:
    """
    Reddit data ingestion class for fetching posts and comments
    from financial subreddits for sentiment analysis.
    """
    
    def __init__(self):
        """
        Initialize Reddit API client with credentials from environment variables.
        
        Required environment variables:
        - REDDIT_CLIENT_ID
        - REDDIT_CLIENT_SECRET
        - REDDIT_USER_AGENT
        """
        self.reddit = self._initialize_reddit()
        
        # Financial subreddits to monitor
        self.financial_subreddits = [
            'stocks', 'investing', 'SecurityAnalysis', 'ValueInvesting',
            'StockMarket', 'options', 'pennystocks', 'wallstreetbets',
            'financialindependence', 'dividends'
        ]
    
    def _initialize_reddit(self) -> praw.Reddit:
        """Initialize PRAW Reddit instance"""
        try:
            reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'ai-trading-agent')
            )
            
            logger.info("Reddit API connection established successfully")
            return reddit
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {e}")
            logger.info("Please set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT environment variables")
            raise
    
    def fetch_subreddit_posts(
        self,
        subreddit_name: str,
        limit: int = 100,
        time_filter: str = 'day',
        sort: str = 'hot'
    ) -> List[RedditPost]:
        """
        Fetch posts from a specific subreddit.
        
        Args:
            subreddit_name: Name of the subreddit (without r/)
            limit: Number of posts to fetch
            time_filter: Time filter ('hour', 'day', 'week', 'month', 'year', 'all')
            sort: Sort method ('hot', 'new', 'top', 'rising')
            
        Returns:
            List of RedditPost objects
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Choose sorting method
            if sort == 'hot':
                posts = subreddit.hot(limit=limit)
            elif sort == 'new':
                posts = subreddit.new(limit=limit)
            elif sort == 'top':
                posts = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort == 'rising':
                posts = subreddit.rising(limit=limit)
            else:
                posts = subreddit.hot(limit=limit)
            
            reddit_posts = []
            for post in posts:
                reddit_post = RedditPost(
                    id=post.id,
                    title=post.title,
                    selftext=post.selftext,
                    score=post.score,
                    upvote_ratio=post.upvote_ratio,
                    num_comments=post.num_comments,
                    created_utc=datetime.fromtimestamp(post.created_utc),
                    subreddit=post.subreddit.display_name,
                    url=post.url,
                    author=str(post.author) if post.author else '[deleted]',
                    flair=post.link_flair_text
                )
                reddit_posts.append(reddit_post)
            
            logger.info(f"Fetched {len(reddit_posts)} posts from r/{subreddit_name}")
            return reddit_posts
            
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            return []
    
    def fetch_post_comments(
        self,
        post_id: str,
        limit: int = 50
    ) -> List[RedditComment]:
        """
        Fetch comments for a specific post.
        
        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to fetch
            
        Returns:
            List of RedditComment objects
        """
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "load more comments"
            
            comments = []
            for comment in submission.comments.list()[:limit]:
                if hasattr(comment, 'body') and comment.body != '[deleted]':
                    reddit_comment = RedditComment(
                        id=comment.id,
                        body=comment.body,
                        score=comment.score,
                        created_utc=datetime.fromtimestamp(comment.created_utc),
                        author=str(comment.author) if comment.author else '[deleted]',
                        parent_id=comment.parent_id
                    )
                    comments.append(reddit_comment)
            
            logger.info(f"Fetched {len(comments)} comments for post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            return []
    
    def search_stock_mentions(
        self,
        subreddit_name: str,
        symbols: List[str],
        limit: int = 100,
        time_filter: str = 'day'
    ) -> Dict[str, List[RedditPost]]:
        """
        Search for posts mentioning specific stock symbols.
        
        Args:
            subreddit_name: Subreddit to search in
            symbols: List of stock symbols to search for
            limit: Number of posts to search through
            time_filter: Time filter for search
            
        Returns:
            Dictionary mapping symbols to lists of posts mentioning them
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            results = {}
            
            for symbol in symbols:
                # Search for posts containing the symbol
                search_query = f"${symbol} OR {symbol}"
                posts = list(subreddit.search(search_query, time_filter=time_filter, limit=limit))
                
                symbol_posts = []
                for post in posts:
                    reddit_post = RedditPost(
                        id=post.id,
                        title=post.title,
                        selftext=post.selftext,
                        score=post.score,
                        upvote_ratio=post.upvote_ratio,
                        num_comments=post.num_comments,
                        created_utc=datetime.fromtimestamp(post.created_utc),
                        subreddit=post.subreddit.display_name,
                        url=post.url,
                        author=str(post.author) if post.author else '[deleted]',
                        flair=post.link_flair_text
                    )
                    symbol_posts.append(reddit_post)
                
                results[symbol] = symbol_posts
                logger.info(f"Found {len(symbol_posts)} posts mentioning {symbol}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching for stock mentions: {e}")
            return {}
    
    def get_trending_stocks(
        self,
        subreddit_names: List[str] = None,
        limit: int = 100
    ) -> Dict[str, int]:
        """
        Analyze posts to find trending stock symbols.
        
        Args:
            subreddit_names: List of subreddits to analyze
            limit: Number of posts to analyze per subreddit
            
        Returns:
            Dictionary of stock symbols and their mention counts
        """
        if subreddit_names is None:
            subreddit_names = ['stocks', 'investing', 'wallstreetbets']
        
        stock_mentions = {}
        
        for subreddit_name in subreddit_names:
            try:
                posts = self.fetch_subreddit_posts(subreddit_name, limit=limit)
                
                for post in posts:
                    content = f"{post.title} {post.selftext}".upper()
                    
                    # Simple regex to find stock symbols ($ followed by 1-5 letters)
                    import re
                    symbols = re.findall(r'\$([A-Z]{1,5})\b', content)
                    
                    for symbol in symbols:
                        stock_mentions[symbol] = stock_mentions.get(symbol, 0) + 1
            
            except Exception as e:
                logger.error(f"Error analyzing r/{subreddit_name}: {e}")
                continue
        
        # Sort by mention count
        trending = dict(sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True))
        logger.info(f"Found {len(trending)} trending stock symbols")
        
        return trending
    
    def extract_stock_symbols(self, text: str) -> List[str]:
        """
        Extract stock symbols from text.
        
        Args:
            text: Text to analyze for stock symbols
            
        Returns:
            List of stock symbols found
        """
        import re
        
        if not text:
            return []
        
        # Find patterns like $AAPL or AAPL stock
        patterns = [
            r'\$([A-Z]{1,5})\b',  # $AAPL
            r'\b([A-Z]{2,5})\s+(?:stock|shares|equity)\b'  # AAPL stock
        ]
        
        symbols = []
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            symbols.extend(matches)
        
        # Remove duplicates and common false positives
        false_positives = {'US', 'USA', 'UK', 'EU', 'CEO', 'CFO', 'IPO', 'ETF', 'GDP', 'API'}
        return list(set([s for s in symbols if s not in false_positives and len(s) <= 5]))
    
    def to_dataframe(self, posts: List[RedditPost]) -> pd.DataFrame:
        """
        Convert list of RedditPost objects to pandas DataFrame.
        
        Args:
            posts: List of RedditPost objects
            
        Returns:
            pandas DataFrame with standardized columns: ['symbol', 'timestamp', 'source', 'text', ...]
        """
        if not posts:
            return pd.DataFrame()
        
        data = []
        for post in posts:
            # Extract stock symbols from title and text
            text_content = f"{post.title} {post.selftext}"
            symbols = self.extract_stock_symbols(text_content)
            symbol = symbols[0] if symbols else None  # Primary symbol
            
            data.append({
                'symbol': symbol,
                'timestamp': post.created_utc,
                'source': f"reddit_{post.subreddit}",
                'text': text_content,
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'subreddit': post.subreddit,
                'url': post.url,
                'author': post.author,
                'flair': post.flair,
                'all_symbols': symbols,
                'symbol_count': len(symbols)
            })
        
        return pd.DataFrame(data)


# Example usage and testing
if __name__ == "__main__":
    # Initialize Reddit ingestion
    reddit_client = RedditIngestion()
    
    # Example: Fetch posts from r/stocks
    posts = reddit_client.fetch_subreddit_posts('stocks', limit=10)
    print(f"Found {len(posts)} posts from r/stocks")
    
    # Convert to DataFrame
    df = reddit_client.to_dataframe(posts)
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Example: Get trending stocks
    trending = reddit_client.get_trending_stocks(limit=50)
    print(f"Trending stocks: {dict(list(trending.items())[:5])}")
