# AI Trading Agent 🤖📈

Production-ready AI trading agent for high-leverage ETF momentum trading with sentiment analysis, technical indicators, and risk management.

## 🎯 Strategy Focus
- **High-Leverage ETFs**: TQQQ, SOXL, LABU momentum patterns
- **Technical Analysis**: RSI(14), MACD(12,26,9), Volume MA(20)
- **Risk Management**: -8% stop loss, +20% take profit, 50% partial sells
- **Sentiment Integration**: Reddit crowd psychology analysis

## 🚀 Quick Start

```bash
# Run full trading cycle
python src/main.py

# Test integration
python src/main.py --mode test

# Collect data only
python src/main.py --mode collect

# Generate signals only
python src/main.py --mode signals
```

## 📁 Project Structure

```
ai-trading-agent/
├── README.md                     # This file
├── pyproject.toml                # Dependencies
├── .env                          # API credentials
│
├── src/                          # 🔧 Core Application
│   ├── main.py                   # Main entry point
│   ├── ingestion/                # Data collection modules
│   ├── signals/                  # Signal generation engine
│   └── fundamentals/             # Fundamental analysis
│
├── strategies/                   # 📈 Trading Strategies
│   └── momentum_strategy.py      # Main momentum strategy
│
├── scripts/                      # 🔄 Operational Scripts
│   ├── final_integration_test.py # Integration testing
│   └── simple_data_collector.py  # Data collection
│
├── data/                         # 📊 Live Data
│   ├── trading_signals_latest.csv
│   └── trading_data_latest.csv
│
└── docs/                         # 📚 Documentation
    ├── API_SETUP_GUIDE.md
    ├── AI_AGENT_REQUIREMENTS.md
    └── STRATEGY_COMPLETE.md
```

## 🔧 Features

### Data Collection
- **Reddit Sentiment**: Real-time crowd psychology from r/stocks
- **News Analysis**: Multi-source financial news aggregation
- **Technical Data**: Live price/volume data with indicators
- **Fundamental Metrics**: Yahoo Finance + Alpha Vantage integration

### Signal Generation
- **Sentiment Scoring**: AI-powered text analysis
- **Volume Detection**: Price + social volume spikes
- **Technical Triggers**: RSI/MACD/Volume breakouts
- **Unified Decisions**: Weighted signal combination

### Risk Management
- **Stop Loss**: -8% automatic risk control
- **Take Profit**: +20% target with 50% partial sells
- **Position Sizing**: Confidence-based allocation
- **Risk/Reward**: 1:2.5 optimal ratio

## 📊 Live Data Flow

```
Market Data → Signal Engine → Trading Decisions
     ↓              ↓              ↓
Reddit Posts → Sentiment Score → BUY/SELL Signal
News Articles → Volume Analysis → Risk Parameters
Price Data → Technical Triggers → Position Size
```

## 🎮 Usage Examples

```python
# Initialize AI agent
from src.main import AITradingAgent
agent = AITradingAgent()

# Run complete cycle
success = agent.run_full_cycle()

# Check latest signals
signals = pd.read_csv("data/trading_signals_latest.csv")
print(signals[['symbol', 'signal', 'entry_price', 'stop_loss', 'take_profit']])
```

## 🔑 API Configuration

See `docs/API_SETUP_GUIDE.md` for complete setup instructions.

Required environment variables:
```
ALPHA_VANTAGE_API_KEY=your_key
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=your_agent
NEWS_API_KEY=your_key
```

## 📈 Performance

- **Data Collection**: 50+ data points per run
- **Signal Generation**: Real-time momentum detection
- **Risk Management**: Automated position sizing
- **Success Rate**: Optimized for high-leverage ETF patterns

## 🚀 Next Steps

1. **Automated Execution**: Connect to broker API
2. **Backtesting**: Historical performance analysis
3. **Real-time Monitoring**: 24/7 market scanning
4. **Advanced ML**: Neural network signal enhancement

---

**⚠️ Disclaimer**: This is for educational purposes. Always do your own research and manage risk appropriately.
