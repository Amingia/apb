import numpy as np

def compute_features(prices, volumes, orderbook_metrics, news_data):
    """
    Computes numerical features without using pandas.
    Returns a dictionary of current feature values and a historical feature matrix
    for training. Ensures all features are valid numbers (no NaNs or Nulls).
    """
    if len(prices) < 24:
        # Fallback if history is too short
        return fallback_features(orderbook_metrics, news_data), (np.array([]), np.array([]))

    prices_arr = np.array(prices)
    volumes_arr = np.array(volumes)

    # Calculate returns
    returns = np.zeros_like(prices_arr)
    returns[1:] = (prices_arr[1:] - prices_arr[:-1]) / prices_arr[:-1]

    # Calculate Moving Averages (simple implementation)
    ma_short = np.zeros_like(prices_arr)
    ma_long = np.zeros_like(prices_arr)
    short_window = 7
    long_window = 24

    for i in range(len(prices_arr)):
        if i >= short_window - 1:
            ma_short[i] = np.mean(prices_arr[i - short_window + 1 : i + 1])
        else:
            ma_short[i] = np.mean(prices_arr[: i + 1])

        if i >= long_window - 1:
            ma_long[i] = np.mean(prices_arr[i - long_window + 1 : i + 1])
        else:
            ma_long[i] = np.mean(prices_arr[: i + 1])

    # Calculate Volatility (rolling standard deviation of returns)
    volatility = np.zeros_like(returns)
    vol_window = 24
    for i in range(len(returns)):
        if i >= vol_window - 1:
            volatility[i] = np.std(returns[i - vol_window + 1 : i + 1])
        else:
            volatility[i] = np.std(returns[: i + 1]) if i > 0 else 0

    # Build historical feature matrix for training
    # Columns: [Return(t-1), MA_Short(t-1)/Price(t-1), MA_Long(t-1)/Price(t-1), Volatility(t-1), Volume(t-1)]
    # Target: Return(t)
    X = []
    y = []

    # Start from index where we have enough history for long window
    start_idx = long_window
    for i in range(start_idx, len(prices_arr) - 1): # -1 because we need target for next step
        p_prev = prices_arr[i]
        if p_prev <= 0:
            continue

        features_row = [
            returns[i],
            ma_short[i] / p_prev,
            ma_long[i] / p_prev,
            volatility[i],
            volumes_arr[i]
        ]
        X.append(features_row)
        # target is the return for the *next* hour
        y.append(returns[i + 1])

    # Calculate current features (latest index)
    curr_idx = len(prices_arr) - 1
    curr_price = prices_arr[curr_idx]

    # News features
    news_sentiment = 0.0
    headline_count = 0
    if news_data and news_data.get("is_available"):
        headline_count = news_data.get("items_count", 0)
        headlines = news_data.get("headlines", [])
        if headlines:
            news_sentiment = sum(h.get("sentiment", 0) for h in headlines) / len(headlines)

    # Market regime logic based on MA crossover and volatility
    regime = "neutral"
    if curr_price > 0:
        ma_ratio = ma_short[curr_idx] / ma_long[curr_idx] if ma_long[curr_idx] > 0 else 1.0
        if ma_ratio > 1.01 and volatility[curr_idx] > np.percentile(volatility[start_idx:], 70):
            regime = "alcista_volátil"
        elif ma_ratio > 1.01:
            regime = "alcista"
        elif ma_ratio < 0.99 and volatility[curr_idx] > np.percentile(volatility[start_idx:], 70):
            regime = "bajista_volátil"
        elif ma_ratio < 0.99:
            regime = "bajista"

    current_features = {
        # Raw inputs for inference (must match X columns)
        "model_inputs": [
            returns[curr_idx],
            ma_short[curr_idx] / curr_price if curr_price > 0 else 1.0,
            ma_long[curr_idx] / curr_price if curr_price > 0 else 1.0,
            volatility[curr_idx],
            volumes_arr[curr_idx]
        ],
        # Signals for the frontend contract
        "signals": {
            "news_sentiment": float(news_sentiment),
            "headline_count": int(headline_count),
            "market_regime": regime,
            "order_book_imbalance": float(orderbook_metrics.get("imbalance", 0)),
            "spread_bps": float(orderbook_metrics.get("spread_bps", 0)),
            "volume_pressure": float(orderbook_metrics.get("volume_pressure", 0)),
            "confidence": float(max(0.0, 1.0 - volatility[curr_idx] * 10)) # Simple confidence proxy based on low volatility
        }
    }

    return current_features, (np.array(X), np.array(y))

def fallback_features(orderbook_metrics, news_data):
    """Fallback if history is insufficient."""
    return {
        "model_inputs": [0.0, 1.0, 1.0, 0.0, 0.0],
        "signals": {
            "news_sentiment": 0.0,
            "headline_count": 0,
            "market_regime": "neutral",
            "order_book_imbalance": float(orderbook_metrics.get("imbalance", 0)),
            "spread_bps": float(orderbook_metrics.get("spread_bps", 0)),
            "volume_pressure": float(orderbook_metrics.get("volume_pressure", 0)),
            "confidence": 0.0
        }
    }
