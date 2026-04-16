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

    # 2. EMAs (Exponential Moving Averages) - más reactivas que las simples
    def calc_ema(data, span):
        ema = np.zeros_like(data)
        if len(data) > 0:
            ema[0] = data[0]
            alpha = 2 / (span + 1)
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        return ema

    ema_short = calc_ema(prices_arr, 7)
    ema_long = calc_ema(prices_arr, 24)

    # 3. Volatilidad e indicadores de amplitud
    volatility_short = np.zeros_like(returns)
    volatility_long = np.zeros_like(returns)
    amplitude = np.zeros_like(prices_arr)

    for i in range(len(prices_arr)):
        if i > 0:
            window_short = returns[max(0, i - 7 + 1):i + 1]
            window_long = returns[max(0, i - 24 + 1):i + 1]
            volatility_short[i] = np.std(window_short)
            volatility_long[i] = np.std(window_long)

            # Amplitud pseudo-ATR en %
            recent_prices = prices_arr[max(0, i - 24 + 1):i + 1]
            amplitude[i] = (np.max(recent_prices) - np.min(recent_prices)) / prices_arr[i]

    # 4. Momentum y Aceleración
    momentum_1 = returns.copy()
    momentum_3 = np.zeros_like(returns)
    momentum_6 = np.zeros_like(returns)
    momentum_12 = np.zeros_like(returns)
    momentum_24 = np.zeros_like(returns)

    for i in range(1, len(prices_arr)):
        if i >= 3: momentum_3[i] = (prices_arr[i] - prices_arr[i-3]) / prices_arr[i-3]
        if i >= 6: momentum_6[i] = (prices_arr[i] - prices_arr[i-6]) / prices_arr[i-6]
        if i >= 12: momentum_12[i] = (prices_arr[i] - prices_arr[i-12]) / prices_arr[i-12]
        if i >= 24: momentum_24[i] = (prices_arr[i] - prices_arr[i-24]) / prices_arr[i-24]

    accel_momentum = np.zeros_like(returns)
    for i in range(1, len(prices_arr)):
        accel_momentum[i] = momentum_1[i] - momentum_1[i-1]

    # 5. Build historical feature matrix for training
    # Targets: Return(t) for multiple horizons
    X = []
    y = []

    start_idx = 24 # Necesitamos al menos 24 puntos históricos para el momentum_24
    horizon = 24

    for i in range(start_idx, len(prices_arr) - horizon):
        p_prev = prices_arr[i]
        if p_prev <= 0:
            continue

        features_row = [
            log_returns[i],                                   # F1: Retorno logarítmico reciente
            momentum_1[i],                                    # F2: Momentum 1h
            momentum_3[i],                                    # F3: Momentum 3h
            momentum_6[i],                                    # F4: Momentum 6h
            momentum_12[i],                                   # F5: Momentum 12h
            momentum_24[i],                                   # F6: Momentum 24h
            accel_momentum[i],                                # F7: Aceleración del momentum
            (prices_arr[i] - ema_short[i]) / ema_short[i],    # F8: Distancia EMA corta
            (prices_arr[i] - ema_long[i]) / ema_long[i],      # F9: Distancia EMA larga
            volatility_short[i],                              # F10: Volatilidad corta
            volatility_long[i],                               # F11: Volatilidad larga
            amplitude[i],                                     # F12: Amplitud reciente
            np.log1p(volumes_arr[i]),                         # F13: Log Volumen
        ]

        # Validar numéricos
        features_row = [0.0 if not np.isfinite(f) else float(f) for f in features_row]
        X.append(features_row)

        # Objective is to predict the cumulative returns for the next 24 hours
        target_row = []
        for h in range(1, horizon + 1):
            future_price = prices_arr[i + h]
            cum_return = (future_price - p_prev) / p_prev
            target_row.append(0.0 if not np.isfinite(cum_return) else float(cum_return))

        y.append(target_row)

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

    # Market regime logic based on EMA crossover and volatility
    regime = "neutral"
    if curr_price > 0:
        ma_ratio = ema_short[curr_idx] / ema_long[curr_idx] if ema_long[curr_idx] > 0 else 1.0
        vol_threshold = np.percentile(volatility_long[start_idx:], 70) if len(volatility_long) > start_idx else 0.02
        if ma_ratio > 1.01 and volatility_long[curr_idx] > vol_threshold:
            regime = "bullish"
        elif ma_ratio > 1.01:
            regime = "bullish"
        elif ma_ratio < 0.99 and volatility_long[curr_idx] > vol_threshold:
            regime = "bearish"
        elif ma_ratio < 0.99:
            regime = "bearish"

    # Preparar el vector actual (evitar nulos y asegurar que coincida con el shape de X)
    raw_current = [
        log_returns[curr_idx],
        momentum_1[curr_idx],
        momentum_3[curr_idx],
        momentum_6[curr_idx],
        momentum_12[curr_idx],
        momentum_24[curr_idx],
        accel_momentum[curr_idx],
        (curr_price - ema_short[curr_idx]) / ema_short[curr_idx] if ema_short[curr_idx] > 0 else 0.0,
        (curr_price - ema_long[curr_idx]) / ema_long[curr_idx] if ema_long[curr_idx] > 0 else 0.0,
        volatility_short[curr_idx],
        volatility_long[curr_idx],
        amplitude[curr_idx],
        np.log1p(volumes_arr[curr_idx])
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
        "model_inputs": [0.0] * 13,
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
