from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, Watchlist, PortfolioItem
from app.data_fetcher import DataFetcher
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["portfolio"])

# Pydantic Schemas
class WatchlistCreate(BaseModel):
    symbol: str

class PortfolioCreate(BaseModel):
    symbol: str
    shares: float
    average_price: float

# Watchlist endpoints
@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(Watchlist).all()
    res = []
    for item in items:
        try:
            live = DataFetcher.fetch_live_price(item.symbol)
            res.append({
                "id": item.id,
                "symbol": item.symbol,
                "clean_symbol": item.symbol.split(".")[0],
                "price": live["price"],
                "change": live["change"],
                "change_percent": live["change_percent"]
            })
        except Exception:
            res.append({
                "id": item.id,
                "symbol": item.symbol,
                "clean_symbol": item.symbol.split(".")[0],
                "price": 0.0,
                "change": 0.0,
                "change_percent": 0.0
            })
    return res

@router.post("/watchlist")
def add_to_watchlist(data: WatchlistCreate, db: Session = Depends(get_db)):
    sym = DataFetcher.resolve_symbol(data.symbol)
    existing = db.query(Watchlist).filter(Watchlist.symbol == sym).first()
    if existing:
        return {"status": "already_exists", "symbol": sym}
    
    item = Watchlist(symbol=sym)
    db.add(item)
    db.commit()
    return {"status": "success", "symbol": sym}

@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    sym = DataFetcher.resolve_symbol(symbol)
    item = db.query(Watchlist).filter(Watchlist.symbol == sym).first()
    if not item:
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")
    db.delete(item)
    db.commit()
    return {"status": "success"}

# Portfolio endpoints
@router.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    items = db.query(PortfolioItem).all()
    res = []
    total_value = 0.0
    total_cost = 0.0
    
    for item in items:
        live = DataFetcher.fetch_live_price(item.symbol)
        curr_price = live["price"]
        curr_value = item.shares * curr_price
        cost = item.shares * item.average_price
        profit = curr_value - cost
        profit_pct = (profit / cost * 100) if cost > 0 else 0
        
        total_value += curr_value
        total_cost += cost
        
        res.append({
            "id": item.id,
            "symbol": item.symbol,
            "clean_symbol": item.symbol.split(".")[0],
            "shares": item.shares,
            "average_price": item.average_price,
            "current_price": curr_price,
            "current_value": round(curr_value, 2),
            "profit": round(profit, 2),
            "profit_percent": round(profit_pct, 2)
        })
        
    portfolio_profit = total_value - total_cost
    portfolio_profit_pct = (portfolio_profit / total_cost * 100) if total_cost > 0 else 0
    
    return {
        "holdings": res,
        "summary": {
            "total_value": round(total_value, 2),
            "total_profit": round(portfolio_profit, 2),
            "total_profit_percent": round(portfolio_profit_pct, 2)
        }
    }

@router.post("/portfolio")
def add_to_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    sym = DataFetcher.resolve_symbol(data.symbol)
    holding = db.query(PortfolioItem).filter(PortfolioItem.symbol == sym).first()
    if holding:
        new_shares = holding.shares + data.shares
        holding.average_price = ((holding.shares * holding.average_price) + (data.shares * data.average_price)) / new_shares
        holding.shares = new_shares
    else:
        holding = PortfolioItem(
            symbol=sym,
            shares=data.shares,
            average_price=data.average_price
        )
        db.add(holding)
    db.commit()
    return {"status": "success", "symbol": sym}

@router.delete("/portfolio/{symbol}")
def remove_from_portfolio(symbol: str, db: Session = Depends(get_db)):
    sym = DataFetcher.resolve_symbol(symbol)
    holding = db.query(PortfolioItem).filter(PortfolioItem.symbol == sym).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    db.delete(holding)
    db.commit()
    return {"status": "success"}
