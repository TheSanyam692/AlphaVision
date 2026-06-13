import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import PORT, BASE_DIR
from app.database import init_db
from app.routes import stocks, portfolio, assistant


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AlphaVision.Main")

# Init Database
logger.info("Initializing SQLite database...")
init_db()

# Create FastAPI app
app = FastAPI(
    title="AlphaVision AI Stock Prediction Platform",
    description="Bloomberg + TradingView Inspired Financial Intelligence Hub",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(stocks.router)
app.include_router(portfolio.router)
app.include_router(assistant.router)

# Mount Static Files (Frontend SPA)
static_path = os.path.join(BASE_DIR, "static")
if not os.path.exists(static_path):
    os.makedirs(static_path, exist_ok=True)
    
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/")
def read_root():
    """
    Serves the SPA frontend index.html
    """
    index_file = os.path.join(static_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AlphaVision API running. Place index.html inside the static/ folder to load the dashboard UI."}

if __name__ == "__main__":
    logger.info(f"Starting AlphaVision server on port {PORT}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
