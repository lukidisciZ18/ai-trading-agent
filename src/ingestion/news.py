"""
News Data Ingestion Module

This module provides functionality to fetch financial news headlines and articles
from various news APIs for sentiment analysis and market insights.
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
import os
import logging
from dataclasses import dataclass
import time
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Data class for news article information"""
    title: str
    description: str
    content: str
    url: str
    published_at: datetime
    source: str
    author: Optional[str] = None
    url_to_image: Optional[str] = None
    sentiment_score: Optional[float] = None


class NewsIngestion:
    """
    News data ingestion class for fetching financial news from multiple sources.
    Supports NewsAPI, Alpha Vantage News, and web scraping from financial websites.
    """
    
    def __init__(self):
        """
        Initialize news ingestion with API credentials from environment variables.
        
        Required environment variables:
        - NEWS_API_KEY (for NewsAPI.org)
        - ALPHA_VANTAGE_API_KEY (optional, for Alpha Vantage news)
        """
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Base URLs for different news sources
        self.news_api_base = "https://newsapi.org/v2"
        self.alpha_vantage_base = "https://www.alphavantage.co/query"
        
        # Financial news sources
        self.financial_sources = [
            'bloomberg.com',
            'reuters.com',
            'wsj.com',
            'ft.com',
            'cnbc.com',
            'marketwatch.com',
            'yahoo.com',
            'bloomberg',
            'reuters',
            'the-wall-street-journal',
            'financial-times',
            'cnbc',
            'marketwatch',
            'yahoo-finance',
            'business-insider',
            'seeking-alpha'
        ]
        
        # Financial keywords for news filtering
        self.financial_keywords = [
            'stocks', 'market', 'trading', 'investing', 'earnings',
            'revenue', 'profit', 'IPO', 'merger', 'acquisition',
            'Federal Reserve', 'interest rates', 'inflation',
            'GDP', 'economic', 'financial', 'NYSE', 'NASDAQ'
        ]
        
        # Request headers
        self.headers = {
            'User-Agent': 'TradingBot/1.0 (Financial News Aggregator)'
        }
    
    def fetch_newsapi_articles(
        self,
        query: str = None,
        sources: List[str] = None,
        category: str = 'business',
        language: str = 'en',
        sort_by: str = 'publishedAt',
        page_size: int = 100,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[NewsArticle]:
        """
        Fetch articles from NewsAPI.org.
        
        Args:
            query: Keywords or phrases to search for
            sources: List of news sources (comma-separated)
            category: News category ('business', 'general', etc.)
            language: Language code (default: 'en')
            sort_by: Sort order ('publishedAt', 'relevancy', 'popularity')
            page_size: Number of articles to retrieve (max 100)
            from_date: Earliest article date
            to_date: Latest article date
            
        Returns:
            List of NewsArticle objects
        """
        if not self.news_api_key:
            logger.warning("NEWS_API_KEY not set, skipping NewsAPI fetch")
            return []
        
        try:
            # Build parameters
            params = {
                'apiKey': self.news_api_key,
                'language': language,
                'sortBy': sort_by,
                'pageSize': min(page_size, 100)  # API limit
            }
            
            # Add optional parameters
            if query:
                params['q'] = query
                endpoint = f"{self.news_api_base}/everything"
            else:
                endpoint = f"{self.news_api_base}/top-headlines"
                params['category'] = category
            
            if sources:
                params['sources'] = ','.join(sources)
            
            if from_date:
                params['from'] = from_date.isoformat()
            
            if to_date:
                params['to'] = to_date.isoformat()
            
            # Make request
            response = requests.get(endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] != 'ok':
                logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = []
            for article_data in data.get('articles', []):
                # Skip articles with missing essential data
                if not article_data.get('title') or not article_data.get('publishedAt'):
                    continue
                
                try:
                    published_at = datetime.fromisoformat(
                        article_data['publishedAt'].replace('Z', '+00:00')
                    )
                except (ValueError, TypeError):
                    continue
                
                article = NewsArticle(
                    title=article_data['title'],
                    description=article_data.get('description', ''),
                    content=article_data.get('content', ''),
                    url=article_data['url'],
                    published_at=published_at,
                    source=article_data['source']['name'],
                    author=article_data.get('author'),
                    url_to_image=article_data.get('urlToImage')
                )
                articles.append(article)
            
            logger.info(f"Fetched {len(articles)} articles from NewsAPI")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
            return []
    
    def fetch_stock_news(
        self,
        symbol: str,
        sources: List[str] = None,
        days_back: int = 7,
        max_articles: int = 100
    ) -> List[NewsArticle]:
        """
        Fetch news articles mentioning a specific stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'TSLA')
            sources: List of preferred news sources
            days_back: Number of days to look back
            max_articles: Maximum number of articles
            
        Returns:
            List of NewsArticle objects
        """
        # Build search query
        query = f'"{symbol}" OR "${symbol} stock" OR "{symbol} shares"'
        
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        # Use financial sources if none specified
        if sources is None:
            sources = [s for s in self.financial_sources if '.' not in s]  # API source IDs
        
        return self.fetch_newsapi_articles(
            query=query,
            sources=sources,
            from_date=from_date,
            to_date=to_date,
            page_size=max_articles,
            sort_by='publishedAt'
        )
    
    def fetch_alpha_vantage_news(
        self,
        topics: str = 'technology,finance',
        time_from: Optional[str] = None,
        limit: int = 50
    ) -> List[NewsArticle]:
        """
        Fetch news from Alpha Vantage News API.
        
        Args:
            topics: Comma-separated topics (e.g., 'technology,finance,earnings')
            time_from: Start time in YYYYMMDDTHHMM format
            limit: Number of articles (max 1000)
            
        Returns:
            List of NewsArticle objects
        """
        if not self.alpha_vantage_key:
            logger.warning("ALPHA_VANTAGE_API_KEY not set, skipping Alpha Vantage fetch")
            return []
        
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'topics': topics,
                'apikey': self.alpha_vantage_key,
                'limit': min(limit, 1000)  # API limit
            }
            
            if time_from:
                params['time_from'] = time_from
            
            response = requests.get(self.alpha_vantage_base, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return []
            
            articles = []
            for item in data.get('feed', []):
                try:
                    published_at = datetime.strptime(
                        item['time_published'], 
                        '%Y%m%dT%H%M%S'
                    )
                except (ValueError, KeyError):
                    continue
                
                article = NewsArticle(
                    title=item.get('title', ''),
                    description=item.get('summary', ''),
                    content=item.get('summary', ''),  # Alpha Vantage provides summary, not full content
                    url=item.get('url', ''),
                    published_at=published_at,
                    source=item.get('source', 'Alpha Vantage'),
                    author=item.get('authors', [None])[0] if item.get('authors') else None,
                    sentiment_score=float(item.get('overall_sentiment_score', 0))
                )
                articles.append(article)
            
            logger.info(f"Fetched {len(articles)} articles from Alpha Vantage")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")
            return []
    
    def fetch_market_news(
        self,
        category: str = 'market',
        max_articles: int = 50,
        hours_back: int = 24
    ) -> List[NewsArticle]:
        """
        Fetch general market news.
        
        Args:
            category: News category ('market', 'earnings', 'economy')
            max_articles: Maximum number of articles
            hours_back: Hours to look back
            
        Returns:
            List of NewsArticle objects
        """
        # Build query based on category
        queries = {
            'market': 'stock market OR equity market OR trading OR S&P 500 OR Dow Jones OR NASDAQ',
            'earnings': 'earnings OR quarterly results OR financial results',
            'economy': 'economic data OR GDP OR inflation OR Federal Reserve OR interest rates',
            'crypto': 'cryptocurrency OR bitcoin OR ethereum OR blockchain',
            'tech': 'technology stocks OR tech earnings OR Silicon Valley'
        }
        
        query = queries.get(category, queries['market'])
        
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(hours=hours_back)
        
        return self.fetch_newsapi_articles(
            query=query,
            from_date=from_date,
            to_date=to_date,
            page_size=max_articles,
            sort_by='publishedAt'
        )
    
    def scrape_financial_headlines(
        self,
        sources: List[str] = None
    ) -> List[NewsArticle]:
        """
        Scrape headlines from financial websites.
        Note: This is a basic implementation. For production, consider using
        dedicated scraping libraries like Scrapy or BeautifulSoup.
        
        Args:
            sources: List of website URLs to scrape
            
        Returns:
            List of NewsArticle objects
        """
        if sources is None:
            sources = [
                'https://finance.yahoo.com/news/',
                'https://www.marketwatch.com/latest-news',
                'https://www.cnbc.com/finance/'
            ]
        
        articles = []
        
        # This is a placeholder for web scraping functionality
        # In a real implementation, you would use BeautifulSoup or similar
        logger.info("Web scraping functionality placeholder - implement with BeautifulSoup")
        
        return articles
    
    def get_trending_financial_topics(
        self,
        hours_back: int = 24,
        min_mentions: int = 5
    ) -> Dict[str, int]:
        """
        Analyze news articles to find trending financial topics.
        
        Args:
            hours_back: Hours to look back for news
            min_mentions: Minimum mentions for a topic to be considered trending
            
        Returns:
            Dictionary of topics and their mention counts
        """
        # Fetch recent market news
        articles = self.fetch_market_news(hours_back=hours_back, max_articles=200)
        
        # Count keyword mentions
        topic_counts = {}
        
        for article in articles:
            text = f"{article.title} {article.description}".lower()
            
            for keyword in self.financial_keywords:
                if keyword.lower() in text:
                    topic_counts[keyword] = topic_counts.get(keyword, 0) + 1
        
        # Filter by minimum mentions and sort
        trending = {
            topic: count for topic, count in topic_counts.items() 
            if count >= min_mentions
        }
        
        return dict(sorted(trending.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_news_sentiment(
        self,
        articles: List[NewsArticle],
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Basic sentiment analysis of news articles.
        
        Args:
            articles: List of NewsArticle objects
            symbol: Optional stock symbol to focus analysis on
            
        Returns:
            Dictionary with sentiment metrics
        """
        if not articles:
            return {}
        
        # Simple keyword-based sentiment analysis
        positive_words = [
            'gain', 'rise', 'up', 'increase', 'growth', 'profit', 'beat',
            'strong', 'bullish', 'positive', 'optimistic', 'surge', 'rally'
        ]
        
        negative_words = [
            'fall', 'drop', 'down', 'decrease', 'loss', 'miss', 'weak',
            'bearish', 'negative', 'pessimistic', 'crash', 'decline'
        ]
        
        total_articles = len(articles)
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for article in articles:
            text = f"{article.title} {article.description}".lower()
            
            # Filter by symbol if provided
            if symbol and symbol.lower() not in text:
                continue
            
            pos_score = sum(1 for word in positive_words if word in text)
            neg_score = sum(1 for word in negative_words if word in text)
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1
        
        analyzed_articles = positive_count + negative_count + neutral_count
        
        return {
            'total_articles': total_articles,
            'analyzed_articles': analyzed_articles,
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'neutral_articles': neutral_count,
            'positive_ratio': positive_count / analyzed_articles if analyzed_articles > 0 else 0,
            'negative_ratio': negative_count / analyzed_articles if analyzed_articles > 0 else 0,
            'sentiment_score': (positive_count - negative_count) / analyzed_articles if analyzed_articles > 0 else 0
        }
    
    def to_dataframe(self, articles: List[NewsArticle]) -> pd.DataFrame:
        """
        Convert list of NewsArticle objects to pandas DataFrame.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            pandas DataFrame with standardized columns: ['symbol', 'timestamp', 'source', 'text', ...]
        """
        if not articles:
            return pd.DataFrame()
        
        data = []
        for article in articles:
            # Extract stock symbols from title and description
            text_content = f"{article.title} {article.description}"
            symbols = self.extract_stock_symbols_from_text(text_content)
            symbol = symbols[0] if symbols else None  # Primary symbol
            
            data.append({
                'symbol': symbol,
                'timestamp': article.published_at,
                'source': f"news_{article.source.lower().replace(' ', '_')}",
                'text': text_content,
                'title': article.title,
                'description': article.description,
                'content': article.content,
                'url': article.url,
                'published_at': article.published_at,
                'original_source': article.source,
                'author': article.author,
                'url_to_image': article.url_to_image,
                'sentiment_score': article.sentiment_score,
                'all_symbols': symbols,
                'symbol_count': len(symbols)
            })
        
        return pd.DataFrame(data)
    
    def extract_stock_symbols_from_text(self, text: str) -> List[str]:
        """
        Extract stock symbols from news text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of stock symbols found
        """
        import re
        
        if not text:
            return []
        
        # Find patterns like $AAPL, AAPL stock, (NASDAQ: AAPL), etc.
        patterns = [
            r'\$([A-Z]{1,5})\b',  # $AAPL
            r'\b([A-Z]{2,5})\s+(?:stock|shares|equity)\b',  # AAPL stock
            r'\((?:NYSE|NASDAQ|AMEX):\s*([A-Z]{1,5})\)',  # (NASDAQ: AAPL)
            r'\b([A-Z]{2,5})\s+(?:Inc|Corp|Ltd|Co)\b'  # AAPL Inc
        ]
        
        symbols = []
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            symbols.extend(matches)
        
        # Filter out common false positives
        false_positives = {
            'US', 'USA', 'UK', 'EU', 'CEO', 'CFO', 'IPO', 'ETF', 'GDP', 'API',
            'SEC', 'FDA', 'FTC', 'FBI', 'CIA', 'IRS', 'LLC', 'INC', 'CORP', 'LTD'
        }
        
        return list(set([s for s in symbols if s not in false_positives and len(s) <= 5]))


# Example usage and testing
if __name__ == "__main__":
    # Initialize news ingestion
    news_client = NewsIngestion()
    
    # Example: Fetch market news
    market_news = news_client.fetch_market_news(max_articles=10)
    print(f"Found {len(market_news)} market news articles")
    
    # Example: Fetch AAPL news
    aapl_news = news_client.fetch_stock_news('AAPL', max_articles=5)
    print(f"Found {len(aapl_news)} articles about AAPL")
    
    # Example: Analyze sentiment
    if market_news:
        sentiment = news_client.analyze_news_sentiment(market_news)
        print(f"Market sentiment analysis: {sentiment}")
    
    # Example: Get trending topics
    trending = news_client.get_trending_financial_topics()
    print(f"Trending topics: {dict(list(trending.items())[:5])}")
    
    # Convert to DataFrame
    if market_news:
        df = news_client.to_dataframe(market_news)
        print(f"\nNews DataFrame shape: {df.shape}")
        print(f"Sources: {df['source'].unique()}")
