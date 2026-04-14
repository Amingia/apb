import os
import joblib
import numpy as np
from datetime import datetime
from sklearn.ensemble import HistGradientBoostingRegressor

MODEL_FILE = "app/btcusdt_model.joblib"

def get_naive_prediction(current_price, last_prices, num_steps=24):
    """
    Generates a naive prediction: simple continuation with slight drift
    based on the mean return of the recent prices.
    """
    prices = []
    if len(last_prices) >= 24:
        recent = last_prices[-24:]
        returns = [(recent[i] - recent[i-1])/recent[i-1] for i in range(1, len(recent))]
        mean_return = sum(returns) / len(returns)
    else:
        mean_return = 0.0

    current = current_price
    for _ in range(num_steps):
        current = current * (1 + mean_return)
        prices.append(current)

    return prices

def train_and_predict(current_price, current_features, historical_data, news_available, last_timestamps):
    """
    Trains a model locally if data is available, then predicts the next 24 hours.
    Returns the predicted prices, timestamps, and the model mode.
    """
    X, y = historical_data

    # Mode determination
    mode = "hybrid" if news_available else "market_only"

    timestamps = []
    base_time = last_timestamps[-1] if last_timestamps else int(datetime.now().timestamp() * 1000)
    for i in range(1, 25):
        timestamps.append(base_time + i * 3600 * 1000) # Add 1 hour in ms

    if len(X) < 100:
        # Not enough data to train reliably
        return get_naive_prediction(current_price, historical_data[0] if historical_data[0].size > 0 else [], 24), timestamps, "naive", {"name": "HistGradientBoostingRegressor", "version": "1.0", "trained_on_points": 0, "last_trained_at": ""}

    try:
        # Train a fast, robust model for tabular data
        model = HistGradientBoostingRegressor(random_state=42)
        model.fit(X, y)

        # Save model artifact
        joblib.dump(model, MODEL_FILE)

        # Predict recursively 24 steps
        predicted_prices = []
        curr_p = current_price

        # Copy inputs to avoid modifying the original
        curr_inputs = list(current_features["model_inputs"])

        for _ in range(24):
            # Predict the next return
            next_return = model.predict([curr_inputs])[0]

            # Bound the prediction to prevent crazy exponential explosion in recursive steps
            next_return = max(min(next_return, 0.10), -0.10)

            # Calculate next price
            next_p = curr_p * (1 + next_return)
            predicted_prices.append(float(next_p))

            # Update inputs for next step recursively (simplified update)
            # In a full model, we'd recursively update MAs, volatility, etc.
            # For this MVP, we just shift the return and keep others constant as proxies
            curr_inputs[0] = next_return
            curr_p = next_p

        model_info = {
            "name": "HistGradientBoostingRegressor",
            "version": "1.0",
            "trained_on_points": len(X),
            "last_trained_at": datetime.now().isoformat() + "Z"
        }

        return predicted_prices, timestamps, mode, model_info

    except Exception:
        # Fallback if anything fails during training/prediction
        return get_naive_prediction(current_price, historical_data[0] if historical_data[0].size > 0 else [], 24), timestamps, "naive", {"name": "HistGradientBoostingRegressor", "version": "1.0", "trained_on_points": 0, "last_trained_at": ""}
