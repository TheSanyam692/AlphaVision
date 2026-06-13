import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import logging

logger = logging.getLogger("AlphaVision.Sentiment")

# Ensure NLTK vader lexicon is available
try:
    sia = SentimentIntensityAnalyzer()
except Exception:
    logger.info("Downloading NLTK VADER lexicon...")
    try:
        nltk.download("vader_lexicon", quiet=True)
        sia = SentimentIntensityAnalyzer()
    except Exception as e:
        logger.error(f"Failed to load NLTK VADER lexicon: {e}. Falling back to Rule-Based Custom Lexicon.")
        sia = None

# Custom simple rule-based sentiment dictionary if VADER is unavailable
POSITIVE_WORDS = {"buy", "bullish", "profit", "gain", "growth", "high", "upgrade", "outperform", "surge", "beat", "positive", "strong"}
NEGATIVE_WORDS = {"sell", "bearish", "loss", "decline", "low", "downgrade", "underperform", "drop", "miss", "negative", "weak", "slump"}

class SentimentAnalyzer:
    @staticmethod
    def analyze_sentiment(text: str) -> dict:
        """
        Analyzes sentiment of text and returns a score in [-1.0, 1.0]
        and classification: Positive, Neutral, Negative.
        """
        if not text:
            return {"score": 0.0, "sentiment": "NEUTRAL"}
            
        score = 0.0
        
        if sia:
            try:
                scores = sia.polarity_scores(text)
                score = scores["compound"]
            except Exception as e:
                logger.error(f"VADER analysis failed: {e}")
                sia_working = False
            else:
                sia_working = True
        else:
            sia_working = False
            
        if not sia_working:
            # Simple fallback regex/lexicon sentiment calculation
            words = text.lower().split()
            pos_count = sum(1 for w in words if any(pw in w for pw in POSITIVE_WORDS))
            neg_count = sum(1 for w in words if any(nw in w for nw in NEGATIVE_WORDS))
            total = pos_count + neg_count
            if total > 0:
                score = (pos_count - neg_count) / total
            else:
                score = 0.0
                
        # Classification
        if score >= 0.05:
            classification = "POSITIVE"
        elif score <= -0.05:
            classification = "NEGATIVE"
        else:
            classification = "NEUTRAL"
            
        return {
            "score": round(float(score), 4),
            "sentiment": classification
        }

    @classmethod
    def get_news_sentiment(cls, news_articles: list) -> dict:
        """
        Processes list of news articles and returns average score and breakdown.
        """
        if not news_articles:
            return {"score": 0.0, "sentiment": "NEUTRAL", "articles_analyzed": 0}
            
        total_score = 0.0
        breakdown = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        
        for article in news_articles:
            title = article.get("title", "")
            res = cls.analyze_sentiment(title)
            total_score += res["score"]
            breakdown[res["sentiment"]] += 1
            
        avg_score = total_score / len(news_articles)
        
        if avg_score >= 0.05:
            overall = "POSITIVE"
        elif avg_score <= -0.05:
            overall = "NEGATIVE"
        else:
            overall = "NEUTRAL"
            
        return {
            "score": round(avg_score, 4),
            "sentiment": overall,
            "articles_analyzed": len(news_articles),
            "breakdown": breakdown
        }
