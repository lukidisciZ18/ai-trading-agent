# API Setup Guide for AI Trading Agent

## Required API Credentials

To run the data ingestion modules with real data, you need to obtain API credentials from the following services:

### 🔴 **REQUIRED APIs**

#### 1. Reddit API (PRAW) - **FREE**
**What you need:**
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT` (already set to "ai-trading-agent")

**How to get them:**
1. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Fill out the form:
   - **Name**: AI Trading Agent
   - **App type**: Select "script"
   - **Description**: Data collection for trading analysis
   - **About URL**: Leave blank
   - **Redirect URI**: http://localhost:8080 (required but not used)
4. Click "Create app"
5. Note down:
   - **Client ID**: The string under the app name (e.g., "abc123defGHI")
   - **Client Secret**: The "secret" field

#### 2. Twitter API v2 - **FREE Tier Available**
**What you need:**
- `TWITTER_BEARER_TOKEN`

**How to get it:**
1. Go to [https://developer.twitter.com/en/portal/dashboard](https://developer.twitter.com/en/portal/dashboard)
2. Sign up for a Developer Account (may require approval)
3. Create a new App/Project
4. Generate Bearer Token in the "Keys and Tokens" section
5. Copy the Bearer Token

**Note**: Twitter's free tier allows 500,000 tweets per month, which should be sufficient for testing.

#### 3. News API - **FREE Tier Available**
**What you need:**
- `NEWS_API_KEY`

**How to get it:**
1. Go to [https://newsapi.org/register](https://newsapi.org/register)
2. Sign up for a free account
3. Verify your email
4. Copy your API key from the dashboard

**Free tier limits**: 1,000 requests per day, which is good for testing.

### 🟡 **OPTIONAL API**

#### 4. Alpha Vantage API - **FREE**
**What you need:**
- `ALPHA_VANTAGE_API_KEY` (optional, for additional news with sentiment scores)

**How to get it:**
1. Go to [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
2. Enter your email and get free API key
3. Free tier: 25 requests per day

---

## Setup Instructions

### Step 1: Get Your API Keys
Follow the instructions above to obtain:
- ✅ Reddit Client ID & Secret
- ✅ Twitter Bearer Token  
- ✅ News API Key
- 🔄 Alpha Vantage Key (optional)

### Step 2: Update Your .env File
Edit the `.env` file in your project root and replace the placeholder values:

```bash
# Replace these with your actual API credentials
REDDIT_CLIENT_ID=your_actual_client_id_here
REDDIT_CLIENT_SECRET=your_actual_client_secret_here
REDDIT_USER_AGENT=ai-trading-agent

TWITTER_BEARER_TOKEN=your_actual_bearer_token_here

NEWS_API_KEY=your_actual_news_api_key_here

# Optional
ALPHA_VANTAGE_API_KEY=your_actual_alpha_vantage_key_here
```

### Step 3: Test Your Setup
Run the test script to verify everything works:

```bash
poetry run python -c "
from src.ingestion.reddit import RedditIngestion
from src.ingestion.twitter import TwitterIngestion  
from src.ingestion.news import NewsIngestion

print('Testing Reddit API...')
reddit = RedditIngestion()
posts = reddit.fetch_posts('stocks', limit=5)
print(f'✅ Reddit: Found {len(posts)} posts')

print('Testing Twitter API...')
twitter = TwitterIngestion()
tweets = twitter.search_stock_tweets('AAPL', max_results=5)
print(f'✅ Twitter: Found {len(tweets)} tweets')

print('Testing News API...')
news = NewsIngestion()
articles = news.fetch_market_news(max_articles=5)
print(f'✅ News: Found {len(articles)} articles')

print('🎉 All APIs working!')
"
```

---

## What Each API Provides

### 📱 **Reddit Data**
- **Subreddits**: r/stocks, r/investing, r/SecurityAnalysis, etc.
- **Content**: Post titles, text content, comments
- **Metrics**: Upvotes, downvotes, comment counts
- **Timing**: Real-time and historical posts
- **Symbols**: Extract from $TICKER mentions

### 🐦 **Twitter Data**
- **Content**: Tweets mentioning stocks/trading
- **Metrics**: Likes, retweets, replies, quotes
- **Timing**: Real-time tweets (last 7 days for free tier)
- **Sources**: Financial influencers, news accounts
- **Symbols**: Extract from $TICKER cashtags

### 📰 **News Data**
- **Sources**: Major financial news outlets
- **Content**: Headlines, descriptions, full articles
- **Timing**: Real-time and historical articles
- **Symbols**: Extract from article content
- **Sentiment**: Basic sentiment analysis

### 📊 **Alpha Vantage News** (Optional)
- **Content**: Financial news with sentiment scores
- **Timing**: Real-time updates
- **Sentiment**: Pre-calculated sentiment scores
- **Topics**: Categorized by financial topics

---

## Cost Summary

| Service | Free Tier | Paid Plans |
|---------|-----------|------------|
| **Reddit** | Unlimited* | N/A |
| **Twitter** | 500K tweets/month | $100+/month |
| **News API** | 1,000 requests/day | $449+/month |
| **Alpha Vantage** | 25 requests/day | $49.99+/month |

*Reddit has rate limits but they're generous for individual use

---

## Next Steps

1. **Get API credentials** from the services above
2. **Update your .env file** with real credentials
3. **Run the test script** to verify everything works
4. **Start collecting data** for your trading analysis!

Your AI trading agent will then have access to real-time data from Reddit, Twitter, and financial news sources! 🚀
