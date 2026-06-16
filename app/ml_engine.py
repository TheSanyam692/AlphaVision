import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta

# Import ML libraries with fallbacks
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("TradeUp.MLEngine")

# PyTorch Deep Learning Modules if Torch is available
if TORCH_AVAILABLE:
    class LSTMModel(nn.Module):
        def __init__(self, input_dim, hidden_dim=32, num_layers=2):
            super().__init__()
            self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
            self.fc = nn.Linear(hidden_dim, 4)  # Predict Open, High, Low, Close
            
        def forward(self, x):
            # x shape: [batch, seq_len, features]
            out, _ = self.lstm(x)
            # Take the last sequence output
            out = out[:, -1, :]
            return self.fc(out)

    class TransformerModel(nn.Module):
        def __init__(self, input_dim, d_model=32, nhead=4, num_layers=2):
            super().__init__()
            self.input_proj = nn.Linear(input_dim, d_model)
            encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=64, batch_first=True)
            self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
            self.fc = nn.Linear(d_model, 4)
            
        def forward(self, x):
            x = self.input_proj(x)
            out = self.transformer_encoder(x)
            out = out[:, -1, :]
            return self.fc(out)

class EnsemblePredictor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_cols = None
        self.is_trained = False
        self.feature_importances = {}
        
        # Scikit fallback models
        self.fallback_rf = RandomForestRegressor(n_estimators=50, random_state=42)
        self.fallback_gb = GradientBoostingRegressor(n_estimators=50, random_state=42)
        
        # Models
        self.xgb_model = None
        self.lgb_model = None
        self.lstm_model = None
        self.trans_model = None

    def _prepare_data(self, df: pd.DataFrame, target_col: str = "close"):
        """
        Creates target variables for next-day predictions and splits into features and targets.
        """
        # Align targets for next-day prediction (Shift back by 1)
        targets = pd.DataFrame({
            "target_open": df["open"].shift(-1),
            "target_high": df["high"].shift(-1),
            "target_low": df["low"].shift(-1),
            "target_close": df["close"].shift(-1)
        })
        
        # Select all engineered feature columns (excluding dates and targets)
        exclude = ["date", "open", "high", "low", "close", "volume"]
        self.feature_cols = [c for c in df.columns if c not in exclude]
        
        X = df[self.feature_cols].copy()
        
        # Join and drop the last row which won't have a target
        data = pd.concat([X, targets], axis=1)
        data = data.dropna()
        
        return data[self.feature_cols], data[["target_open", "target_high", "target_low", "target_close"]]

    def train(self, df: pd.DataFrame):
        """
        Trains the ensemble model components using the historical dataset.
        """
        if len(df) < 50:
            logger.warning("Dataset is too small for robust training.")
            return False
            
        X, Y = self._prepare_data(df)
        
        # Scale Features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=self.feature_cols)
        
        # 1. Train Fallbacks & Calculate Feature Importances
        self.fallback_rf.fit(X_scaled, Y["target_close"])
        self.fallback_gb.fit(X_scaled, Y["target_close"])
        
        # Populate Feature Importances
        importances = self.fallback_rf.feature_importances_
        indices = np.argsort(importances)[::-1]
        self.feature_importances = {self.feature_cols[i]: float(importances[i]) for i in indices[:10]}

        # 2. Train XGBoost
        if XGB_AVAILABLE:
            try:
                # We need multi-output wrapper or train 4 separate models
                self.xgb_model = {}
                for target in Y.columns:
                    model = xgb.XGBRegressor(n_estimators=50, max_depth=5, learning_rate=0.1, random_state=42)
                    model.fit(X_scaled, Y[target])
                    self.xgb_model[target] = model
                logger.info("XGBoost trained successfully.")
            except Exception as e:
                logger.error(f"XGBoost training failed: {e}")
                self.xgb_model = None

        # 3. Train LightGBM
        if LGBM_AVAILABLE:
            try:
                self.lgb_model = {}
                for target in Y.columns:
                    model = lgb.LGBMRegressor(n_estimators=50, max_depth=5, random_state=42, verbose=-1)
                    model.fit(X_scaled, Y[target])
                    self.lgb_model[target] = model
                logger.info("LightGBM trained successfully.")
            except Exception as e:
                logger.error(f"LightGBM training failed: {e}")
                self.lgb_model = None

        # 4. Train Deep Learning models (LSTM & Transformer)
        if TORCH_AVAILABLE:
            try:
                # Prepare sequence dataset (seq_len = 10)
                seq_len = 10
                X_seq, Y_seq = [], []
                for i in range(len(X_scaled) - seq_len):
                    X_seq.append(X_scaled[i:i+seq_len])
                    Y_seq.append(Y.iloc[i+seq_len].values)
                
                if len(X_seq) > 10:
                    X_seq = torch.tensor(np.array(X_seq), dtype=torch.float32)
                    Y_seq = torch.tensor(np.array(Y_seq), dtype=torch.float32)
                    
                    dataset = TensorDataset(X_seq, Y_seq)
                    loader = DataLoader(dataset, batch_size=16, shuffle=True)
                    
                    # Train LSTM
                    self.lstm_model = LSTMModel(input_dim=len(self.feature_cols))
                    optimizer = torch.optim.Adam(self.lstm_model.parameters(), lr=0.01)
                    criterion = nn.MSELoss()
                    
                    self.lstm_model.train()
                    for epoch in range(5):
                        for bx, by in loader:
                            optimizer.zero_grad()
                            pred = self.lstm_model(bx)
                            loss = criterion(pred, by)
                            loss.backward()
                            optimizer.step()
                            
                    # Train Transformer
                    self.trans_model = TransformerModel(input_dim=len(self.feature_cols))
                    optimizer_t = torch.optim.Adam(self.trans_model.parameters(), lr=0.01)
                    
                    self.trans_model.train()
                    for epoch in range(5):
                        for bx, by in loader:
                            optimizer_t.zero_grad()
                            pred = self.trans_model(bx)
                            loss = criterion(pred, by)
                            loss.backward()
                            optimizer_t.step()
                            
                    logger.info("Deep learning models (LSTM & Transformer) trained successfully.")
            except Exception as e:
                logger.error(f"Deep learning training failed: {e}")
                self.lstm_model = None
                self.trans_model = None

        self.is_trained = True
        return True

    def predict(self, df: pd.DataFrame) -> dict:
        """
        Generates predictions for the next trading day.
        """
        if not self.is_trained or self.feature_cols is None:
            # Auto-train if not yet trained
            self.train(df)
            
        last_row = df[self.feature_cols].iloc[-1:].copy()
        last_row_scaled = self.scaler.transform(last_row)
        
        # Calculate base predictions
        pred_dict = {
            "open": [], "high": [], "low": [], "close": []
        }
        
        # Weights
        # 0.35 XGB, 0.35 LGBM, 0.15 LSTM, 0.15 Transformer
        # If fallbacks are used, adjust weights
        
        # Fallback targets predictions
        rf_close = float(self.fallback_rf.predict(last_row_scaled)[0])
        gb_close = float(self.fallback_gb.predict(last_row_scaled)[0])
        
        # Initialize default predictions with fallbacks
        curr_price = float(df["close"].iloc[-1])
        base_close = 0.5 * rf_close + 0.5 * gb_close
        
        # Distribute targets relative to current price to prevent unrealistic outputs
        pred_open = base_close
        pred_high = base_close * 1.01
        pred_low = base_close * 0.99
        pred_close = base_close
        
        targets_pred = {
            "open": [pred_open],
            "high": [pred_high],
            "low": [pred_low],
            "close": [pred_close]
        }
        
        # XGBoost prediction
        if self.xgb_model:
            for target in ["open", "high", "low", "close"]:
                val = float(self.xgb_model[f"target_{target}"].predict(last_row_scaled)[0])
                targets_pred[target].append(val)
                
        # LightGBM prediction
        if self.lgb_model:
            for target in ["open", "high", "low", "close"]:
                val = float(self.lgb_model[f"target_{target}"].predict(last_row_scaled)[0])
                targets_pred[target].append(val)

        # Deep learning modules prediction
        if TORCH_AVAILABLE and self.lstm_model and self.trans_model:
            try:
                # Need last 10 steps
                last_10 = df[self.feature_cols].iloc[-10:].copy()
                last_10_scaled = self.scaler.transform(last_10)
                input_tensor = torch.tensor(np.array([last_10_scaled]), dtype=torch.float32)
                
                self.lstm_model.eval()
                self.trans_model.eval()
                with torch.no_grad():
                    lstm_out = self.lstm_model(input_tensor).numpy()[0]
                    trans_out = self.trans_model(input_tensor).numpy()[0]
                    
                    for i, target in enumerate(["open", "high", "low", "close"]):
                        targets_pred[target].append(float(lstm_out[i]))
                        targets_pred[target].append(float(trans_out[i]))
            except Exception as e:
                logger.error(f"Deep Learning prediction runtime error: {e}")

        # Compute dynamic weights ensemble
        final_preds = {}
        for target in ["open", "high", "low", "close"]:
            vals = targets_pred[target]
            # Average predictions
            final_preds[target] = float(np.mean(vals))

        # Prediction interval (Standard deviation of forecasts)
        all_close_preds = targets_pred["close"]
        std_dev = np.std(all_close_preds) if len(all_close_preds) > 1 else (final_preds["close"] * 0.015)
        
        # Confidence Score: 0 to 100 based on standard error
        rel_std = std_dev / final_preds["close"]
        confidence = max(50.0, min(98.5, 100.0 - (rel_std * 500)))
        
        # Risk Score: Volatility and downside potential
        recent_vol = float(df["close"].pct_change().iloc[-20:].std() * np.sqrt(252) * 100)
        risk = max(10.0, min(95.0, recent_vol * 1.5))
        
        # Recommendation
        pct_change = ((final_preds["close"] - curr_price) / curr_price) * 100
        if pct_change > 1.5 and confidence > 70:
            rec = "BUY"
            bullish_prob = max(60, int(50 + pct_change * 15))
            bearish_prob = 100 - bullish_prob
        elif pct_change < -1.5:
            rec = "SELL"
            bearish_prob = max(60, int(50 + abs(pct_change) * 15))
            bullish_prob = 100 - bearish_prob
        else:
            rec = "HOLD"
            bullish_prob = 50 + int(pct_change * 5)
            bearish_prob = 100 - bullish_prob

        # Keep probability in range [5, 95]
        bullish_prob = max(5, min(95, bullish_prob))
        bearish_prob = max(5, min(95, bearish_prob))

        return {
            "predicted_open": float(round(final_preds["open"], 2)),
            "predicted_high": float(round(final_preds["high"], 2)),
            "predicted_low": float(round(final_preds["low"], 2)),
            "predicted_close": float(round(final_preds["close"], 2)),
            "confidence_score": float(round(confidence, 1)),
            "prediction_interval": {
                "lower": float(round(final_preds["close"] - 1.96 * std_dev, 2)),
                "upper": float(round(final_preds["close"] + 1.96 * std_dev, 2))
            },
            "risk_score": float(round(risk, 1)),
            "recommendation": rec,
            "bullish_probability": int(bullish_prob),
            "bearish_probability": int(bearish_prob)
        }
