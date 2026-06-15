from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db, PredictionRecord
from app.data_fetcher import DataFetcher
from app.sentiment import SentimentAnalyzer
from app.features import generate_features
from app.ml_engine import EnsemblePredictor
from pydantic import BaseModel
import re

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

class MessageInput(BaseModel):
    message: str
    symbol: str = "AAPL"

@router.post("/query")
def query_assistant(data: MessageInput, db: Session = Depends(get_db)):
    msg = data.message.lower().strip()
    sym = data.symbol.upper().strip()
    
    # Simple regulatory stock extract via regex
    match = re.search(r'\b[a-zA-Z]{3,5}\b', data.message)
    if match:
        potential_sym = match.group(0).upper()
        # Avoid matching words like "what", "show", "help"
        if potential_sym not in ["WHAT", "SHOW", "HELP", "PORT", "NEWS", "RISK"]:
            sym = potential_sym

    # Fallback to general AAPL stock details if needed
    try:
        df = DataFetcher.fetch_historical_prices(sym, period="3mo")
        live = DataFetcher.fetch_live_price(sym)
        news = DataFetcher.fetch_news(sym)
        sentiment = SentimentAnalyzer.get_news_sentiment(news)
        feat_df = generate_features(df)
        predictor = EnsemblePredictor()
        pred = predictor.predict(feat_df)
    except Exception as e:
        return {
            "reply": f"I had trouble gathering real-time metrics for {sym}. Please make sure it is a valid ticker symbol.",
            "symbol": sym
        }

    # Intelligent template queries response
    if "risk" in msg:
        reply = (
            f"The current risk score for **{sym}** is **{pred['risk_score']}/100**. "
            f"This is derived from a historical annualized volatility. The prediction confidence interval ranges from "
            f"${pred['prediction_interval']['lower']} to ${pred['prediction_interval']['upper']}. "
            f"My recommendation is currently **{pred['recommendation']}**."
        )
    elif "news" in msg or "sentiment" in msg:
        reply = (
            f"The overall sentiment for **{sym}** is **{sentiment['sentiment']}** with an NLP score of "
            f"**{sentiment['score']}** (based on {sentiment['articles_analyzed']} articles). "
            f"Recent headlines indicate a {sentiment['breakdown']['POSITIVE']} positive, "
            f"{sentiment['breakdown']['NEUTRAL']} neutral, and {sentiment['breakdown']['NEGATIVE']} negative distribution."
        )
    elif "predict" in msg or "tomorrow" in msg or "future" in msg:
        reply = (
            f"My ensemble architecture predicts the following next-day values for **{sym}**:\n"
            f"• **Close Price**: ${pred['predicted_close']}\n"
            f"• **Expected Range**: ${pred['predicted_low']} - ${pred['predicted_high']}\n"
            f"• **Signal**: {pred['recommendation']} (Confidence: {pred['confidence_score']}%)\n"
            f"• **Bullish Probability**: {pred['bullish_probability']}%\n"
            f"• **Bearish Probability**: {pred['bearish_probability']}%"
        )
    elif "portfolio" in msg or "buy" in msg or "hold" in msg or "sell" in msg:
        reply = (
            f"Based on technical signals, {sym} triggers a **{pred['recommendation']}** rating. "
            f"The MACD & RSI metrics are backing this. Make sure to hedge with target stops at ${pred['predicted_low']}."
        )
    else:
        reply = (
            f"Hi! I am your TradeUp AI Markets Assistant. Analyzing **{sym}**:\n"
            f"• Live price: ₹{live['price']} ({live['change_percent']}%)\n"
            f"• AI signal: **{pred['recommendation']}** (Confidence: {pred['confidence_score']}%)\n"
            f"• Next-day Predicted Close: ₹{pred['predicted_close']}\n"
            f"Ask me about: 'risk analysis', 'sentiment indicators', or 'price predictions'!"
        )

    return {
        "reply": reply,
        "symbol": sym
    }
