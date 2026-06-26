import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/tradego.db")

# Cache TTL (in seconds)
CACHE_TTL = 3600  # 1 hour cache for stock prices & news

# API Keys (Fallback/Dummy allowed for default usage, but user can override via env)
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "demo")
POLYGON_KEY = os.getenv("POLYGON_KEY", "")
FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")

# App Info
APP_NAME = "TradeGo"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
PORT = int(os.getenv("PORT", 8000))
