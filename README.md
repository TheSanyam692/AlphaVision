# TradeGo - AI Powered Stock Intelligence Platform

TradeGo is a production-ready financial analytics and next-day stock price forecasting dashboard. It combines a high-performance **FastAPI backend** (serving ML prediction APIs and NLP news sentiment analysis) with a stunning **Bloomberg-style dark mode Vanilla CSS Single Page Application (SPA)**.

---

## Technical Stack & Architecture

### Backend
- **Framework**: FastAPI (Asynchronous, performance-tuned routing)
- **Database**: SQLite (SQLAlchemy ORM for portfolios, watchlists, predictions, and news cache)
- **Ensemble ML Architecture**: Weighted combination of:
  1. **XGBoost Regressor** (for tabular feature correlation)
  2. **LightGBM Regressor** (fast leaf-wise tree boosting)
  3. **LSTM Time Series Neural Network** (temporal dependencies via PyTorch)
  4. **Transformer Network** (attention-based contextual models)
  *(Note: Dynamic structural fallback to Scikit-Learn regressors is implemented to prevent execution faults if specific deep learning libraries are not installed)*
- **NLP Sentiment Engine**: NLTK VADER analyzer with automatic RSS/Yahoo news feeds collection.
- **Feature Engineering**: Over 50 engineered indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR, VWAP, On-Balance Volume, lags, and rolling standard deviation).

### Frontend
- Immersive Bloomberg + TradingView theme designed with pure **Vanilla CSS** and HTML5.
- Glassmorphism overlays, real-time status glow markers, and micro-animations.
- Interactive charting powered by **ApexCharts** (Candlestick, rolling predictions, and backtest comparison overlay).
- **Web Speech API** Voice command integration ("Analyze Tesla", "Predict Apple").
- Smart AI Chatbot drawer for general market assistance.

---

## Installation & Setup

### Option 1: Docker (Recommended - Immediate Production Run)
Ensure you have Docker and Docker Compose installed.

1. Clone or copy this repository to your machine.
2. In the project root directory, run:
   ```bash
   docker-compose up --build
   ```
3. Open your browser and navigate to: [http://localhost:8000](http://localhost:8000)

---

### Option 2: Local Manual Setup (Python Virtual Env)

1. Create a Python 3.10+ virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   python app/main.py
   ```
4. Access the web dashboard at: [http://localhost:8000](http://localhost:8000)

---

## Interactive Walkthrough & Voice Queries

- **Search / Command Bar**: Enter ticker symbol (e.g. `AAPL`, `TSLA`, `NVDA`) and press **Analyze**.
- **Voice Search**: Click the microphone icon next to the search bar and speak your query clearly (e.g., *"Predict Microsoft"* or *"Tesla"*).
- **Backtesting tab**: Toggle the chart tab to "Backtest Engine" to evaluate performance (RMSE, MAE, MAPE, directional accuracy).
- **AI Markets Assistant**: Click the chat button on the bottom right to start a conversation about prediction risk, news analysis, or trading indicators.
