#!/usr/bin/env python3
"""
Sentiment Analysis Engine for AI Trading Agent using VADER

Clean and simple sentiment analysis using the VADER library,
specifically designed for social media text analysis.
"""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def score_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a 'sentiment' column to any DataFrame with a 'text' field.
    Sentiment is the compound VADER score (-1 to +1).
    
    Args:
        df: DataFrame with 'text' column
        
    Returns:
        DataFrame with added 'sentiment' column
    """
    if 'text' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'text' column")
    
    df = df.copy()
    df['sentiment'] = df['text'].apply(lambda t: analyzer.polarity_scores(t)['compound'])
    return df


# Example usage and testing
if __name__ == "__main__":
    # Test with sample data
    test_data = pd.DataFrame({
        'text': [
            'TQQQ is bullish and breaking out! 🚀',
            'SOXL looks bearish, might crash soon',
            'LABU is neutral, waiting for signals',
            'Amazing momentum in tech stocks today!'
        ]
    })
    
    # Apply sentiment scoring
    result = score_sentiment(test_data)
    print("Sentiment Analysis Results:")
    print(result[['text', 'sentiment']])
    
    print(f"\nAverage sentiment: {result['sentiment'].mean():.3f}")
