import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def score_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Return df with a 'sentiment' column scored by VADER.
    Expects a 'text' column.
    """
    if df is None or df.empty or 'text' not in df.columns:
        return pd.DataFrame({'sentiment': [0.0]})
    sia = SentimentIntensityAnalyzer()
    scores = df['text'].astype(str).apply(lambda t: sia.polarity_scores(t)['compound'])
    out = df.copy()
    out['sentiment'] = scores
    return out
