import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from app.config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Watchlist(Base):
    __tablename__ = "watchlist"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)

class PortfolioItem(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    shares = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, default=datetime.datetime.utcnow)

class PredictionRecord(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    prediction_date = Column(DateTime, default=datetime.datetime.utcnow)
    target_date = Column(DateTime, nullable=False)
    
    current_price = Column(Float, nullable=False)
    predicted_open = Column(Float, nullable=False)
    predicted_high = Column(Float, nullable=False)
    predicted_low = Column(Float, nullable=False)
    predicted_close = Column(Float, nullable=False)
    
    confidence_score = Column(Float, nullable=False)  # 0 to 100
    risk_score = Column(Float, nullable=False)        # 0 to 100
    recommendation = Column(String, nullable=False)   # BUY, HOLD, SELL
    sentiment_score = Column(Float, nullable=False)   # -1 to 1

class NewsCache(Base):
    __tablename__ = "news_cache"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    source = Column(String, nullable=True)
    sentiment = Column(String, nullable=False)        # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float, nullable=False)   # -1 to 1
    published_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

class MarketDataCache(Base):
    __tablename__ = "market_data_cache"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
