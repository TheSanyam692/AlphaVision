import pandas as pd
import numpy as np

def generate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a DataFrame with [date, open, high, low, close, volume] columns,
    and returns a DataFrame containing over 50 engineered technical indicators.
    """
    df = df.copy().sort_values("date").reset_index(drop=True)
    
    # Base indicators
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    
    # 1. Simple Moving Averages (SMA)
    for p in [5, 10, 15, 20, 30, 50, 100, 200]:
        df[f"sma_{p}"] = close.rolling(window=p).mean()
        df[f"sma_ratio_{p}"] = close / df[f"sma_{p}"]
        
    # 2. Exponential Moving Averages (EMA)
    for p in [5, 12, 20, 26, 50, 100]:
        df[f"ema_{p}"] = close.ewm(span=p, adjust=False).mean()
        df[f"ema_ratio_{p}"] = close / df[f"ema_{p}"]

    # 3. Momentum: Relative Strength Index (RSI)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    # Fill NA
    df["rsi_14"] = df["rsi_14"].fillna(50)

    # 4. Trend: MACD (Moving Average Convergence Divergence)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # 5. Volatility: Bollinger Bands
    sma_20 = df["sma_20"]
    std_20 = close.rolling(window=20).std()
    df["bb_upper"] = sma_20 + (std_20 * 2)
    df["bb_lower"] = sma_20 - (std_20 * 2)
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / (sma_20 + 1e-9)
    df["bb_pct"] = (close - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"] + 1e-9)

    # 6. Volatility: ATR (Average True Range)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(window=14).mean()
    df["atr_pct"] = df["atr_14"] / (close + 1e-9)

    # 7. Volume Analysis & VWAP
    # VWAP estimation: Cumulative (Typical Price * Volume) / Cumulative Volume
    typical_price = (high + low + close) / 3
    cum_tp_vol = (typical_price * volume).cumsum()
    cum_vol = volume.cumsum()
    df["vwap"] = cum_tp_vol / (cum_vol + 1e-9)
    df["vwap_ratio"] = close / df["vwap"]
    
    # OBV (On-Balance Volume)
    obv = [0]
    for i in range(1, len(df)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    df["obv"] = obv
    df["obv_ema"] = pd.Series(obv).ewm(span=10).mean()

    # 8. Momentum Indicators: Rate of Change (ROC)
    for p in [5, 10, 20]:
        df[f"roc_{p}"] = close.pct_change(p) * 100

    # 9. High/Low range & price positions
    df["high_low_ratio"] = high / (low + 1e-9)
    df["close_range"] = (close - low) / (high - low + 1e-9)
    
    # 10. Time Series Lag & Return Features
    for l in [1, 2, 3, 5, 10]:
        df[f"return_lag_{l}"] = close.pct_change(l)
        df[f"close_lag_{l}"] = close.shift(l)
        df[f"vol_lag_{l}"] = volume.shift(l)

    # 11. Rolling Volatility
    for p in [5, 10, 21]:
        df[f"rolling_std_{p}"] = close.pct_change().rolling(window=p).std()

    # 12. Dynamic Trend Direction
    df["trend_direction"] = np.where(df["sma_10"] > df["sma_30"], 1, -1)
    df["trend_strength"] = (df["sma_10"] - df["sma_30"]).abs() / (df["sma_30"] + 1e-9)

    # Forward fill/backward fill to guarantee clean data
    df = df.ffill().bfill()
    
    # Safety Check: ensure we have at least 50 columns
    # Let's count features. We have:
    # 8 SMAs + 8 ratios = 16
    # 6 EMAs + 6 ratios = 12
    # RSI = 1
    # MACD, MACD_sig, MACD_hist = 3
    # BB upper, lower, width, pct = 4
    # ATR, ATR_pct = 2
    # VWAP, VWAP_ratio, OBV, OBV_ema = 4
    # ROC (5, 10, 20) = 3
    # high_low_ratio, close_range = 2
    # return_lag, close_lag, vol_lag (x5) = 15
    # rolling_std (x3) = 3
    # trend_direction, trend_strength = 2
    # Total features: 16+12+1+3+4+2+4+3+2+15+3+2 = 67 features! Excellent.
    
    return df
