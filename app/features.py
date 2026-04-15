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

    # 1. Retornos porcentuales y logarítmicos
    returns = np.zeros_like(prices_arr)
    log_returns = np.zeros_like(prices_arr)

    with np.errstate(divide='ignore', invalid='ignore'):
        returns[1:] = (prices_arr[1:] - prices_arr[:-1]) / prices_arr[:-1]
        log_returns[1:] = np.log(prices_arr[1:] / prices_arr[:-1])

    returns[~np.isfinite(returns)] = 0.0
    log_returns[~np.isfinite(log_returns)] = 0.0

    # 2. Moving Averages y distancias
    ma_short_window = 7
    ma_long_window = 24

    ma_short = np.zeros_like(prices_arr)
    ma_long = np.zeros_like(prices_arr)

    for i in range(len(prices_arr)):
        ma_short[i] = np.mean(prices_arr[max(0, i - ma_short_window + 1):i + 1])
        ma_long[i] = np.mean(prices_arr[max(0, i - ma_long_window + 1):i + 1])

    # 3. Volatilidad e indicadores intrabarra básicos
    volatility_short = np.zeros_like(returns)
    volatility_long = np.zeros_like(returns)

    for i in range(len(returns)):
        volatility_short[i] = np.std(returns[max(0, i - ma_short_window + 1):i + 1]) if i > 0 else 0.0
        volatility_long[i] = np.std(returns[max(0, i - ma_long_window + 1):i + 1]) if i > 0 else 0.0

    # 4. Momentum (cambio del retorno sobre ventanas pasadas)
    momentum_7 = np.zeros_like(returns)
    for i in range(7, len(prices_arr)):
        momentum_7[i] = (prices_arr[i] - prices_arr[i-7]) / prices_arr[i-7] if prices_arr[i-7] > 0 else 0.0

    # 5. Build historical feature matrix for training
    # Targets: Return(t) (we predict the next log return for better stability)
    X = []
    y = []

    start_idx = ma_long_window
    for i in range(start_idx, len(prices_arr) - 1): # -1 because we need target for next step
        p_prev = prices_arr[i]
        if p_prev <= 0:
            continue

        features_row = [
            log_returns[i],                                   # F1: Retorno logarítmico reciente
            momentum_7[i],                                    # F2: Momentum 7 periodos
            (prices_arr[i] - ma_short[i]) / ma_short[i],      # F3: Distancia porcentual a la MA corta
            (prices_arr[i] - ma_long[i]) / ma_long[i],        # F4: Distancia porcentual a la MA larga
            volatility_short[i],                              # F5: Volatilidad corta
            volatility_long[i],                               # F6: Volatilidad larga
            volumes_arr[i],                                   # F7: Volumen (escala cruda/log proxy útil para arboles)
        ]

        # Validar numéricos
        features_row = [0.0 if not np.isfinite(f) else float(f) for f in features_row]
        X.append(features_row)

        # Objetivo es predecir el siguiente retorno porcentual
        target_val = returns[i + 1]
        y.append(0.0 if not np.isfinite(target_val) else float(target_val))

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
        vol_threshold = np.percentile(volatility_long[start_idx:], 70) if len(volatility_long) > start_idx else 0.02
        if ma_ratio > 1.01 and volatility_long[curr_idx] > vol_threshold:
            regime = "alcista_volátil"
        elif ma_ratio > 1.01:
            regime = "alcista"
        elif ma_ratio < 0.99 and volatility_long[curr_idx] > vol_threshold:
            regime = "bajista_volátil"
        elif ma_ratio < 0.99:
            regime = "bajista"

    # Preparar el vector actual (evitar nulos y asegurar que coincida con el shape de X)
    raw_current = [
        log_returns[curr_idx],
        momentum_7[curr_idx],
        (curr_price - ma_short[curr_idx]) / ma_short[curr_idx] if ma_short[curr_idx] > 0 else 0.0,
        (curr_price - ma_long[curr_idx]) / ma_long[curr_idx] if ma_long[curr_idx] > 0 else 0.0,
        volatility_short[curr_idx],
        volatility_long[curr_idx],
        volumes_arr[curr_idx]
    ]
    raw_current = [0.0 if not np.isfinite(f) else float(f) for f in raw_current]

    current_features = {
        # Raw inputs for inference (must match X columns)
        "model_inputs": raw_current,
        # Signals for the frontend contract
        "signals": {
            "news_sentiment": float(news_sentiment),
            "headline_count": int(headline_count),
            "market_regime": regime,
            "order_book_imbalance": float(orderbook_metrics.get("imbalance", 0)),
            "spread_bps": float(orderbook_metrics.get("spread_bps", 0)),
            "volume_pressure": float(orderbook_metrics.get("volume_pressure", 0)),
            "confidence": float(max(0.0, 1.0 - volatility_long[curr_idx] * 10)) # Confianza base, será mejorada en app/model.py
        }
    }

    return current_features, (np.array(X), np.array(y))

def fallback_features(orderbook_metrics, news_data):
    """Fallback if history is insufficient."""
    return {
        "model_inputs": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
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
