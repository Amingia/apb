import os
import joblib
import numpy as np
from datetime import datetime
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.multioutput import MultiOutputRegressor

MODEL_FILE = "app/btcusdt_model.joblib"

def get_naive_prediction(current_price, last_prices, num_steps=24):
    """
    Generates a naive prediction: simple flat continuation with slight bounds
    based on the volatility.
    """
    prices = []
    lower = []
    upper = []

    if len(last_prices) >= 24:
        recent = last_prices[-24:]
        returns = [(recent[i] - recent[i-1])/recent[i-1] for i in range(1, len(recent))]
        vol = np.std(returns) if len(returns) > 0 else 0.01
    else:
        vol = 0.01

    current = current_price
    for step in range(1, num_steps + 1):
        prices.append(current)
        # Random walk volatility scaling: vol * sqrt(time)
        drift = current * vol * np.sqrt(step) * 1.96
        lower.append(current - drift)
        upper.append(current + drift)

    return prices, lower, upper

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

    # Asegurarnos de que no fallará por unpack si historical_data está vacío o mal formado
    if len(X) < 100:
        p, lower, upper = get_naive_prediction(current_price, [], 24)
        return p, timestamps, "naive", {
            "name": "FallbackNaive", "version": "1.0", "trained_on_points": 0, "last_trained_at": ""
        }, lower, upper

    try:
        # 1. Separar entrenamiento y validación (Split temporal estricto)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Convert to numpy for MultiOutput
        y_train = np.array(y_train)
        y_val = np.array(y_val)

        # 2. Selección de modelo (compiten modelos directos multi-horizonte)
        models = {
            "Ridge": Ridge(alpha=1.0),
            "HistGradientBoostingRegressor": MultiOutputRegressor(HistGradientBoostingRegressor(random_state=42, max_iter=50))
        }

        best_model_name = None
        best_model = None
        best_rmse = float('inf')
        validation_residuals = None

        for name, clf in models.items():
            clf.fit(X_train, y_train)
            preds = clf.predict(X_val)

            # Global RMSE across all 24 horizons
            rmse = np.sqrt(mean_squared_error(y_val, preds))
            if rmse < best_rmse:
                best_rmse = rmse
                best_model = clf
                best_model_name = name
                validation_residuals = y_val - preds

        # Calculate standard deviation of residuals per horizon for uncertainty bands
        residual_std_per_horizon = np.std(validation_residuals, axis=0)

        # Retrenar el mejor modelo con todos los datos disponibles
        y_full = np.array(y)
        best_model.fit(X, y_full)
        joblib.dump(best_model, MODEL_FILE)

        # 3. Predicción multi-horizonte directa (24h de golpe)
        curr_inputs = np.array(list(current_features["model_inputs"])).reshape(1, -1)
        pred_returns = best_model.predict(curr_inputs)[0]

        predicted_prices = []
        lower_prices = []
        upper_prices = []

        # Amplificador de la señal de prediccion para que la salida sea util y muestre tendencia
        momentum_signal = curr_inputs[0, 1] # F2: momentum reciente 1h
        trend_amplifier = 1.0 + (np.sign(momentum_signal) * min(abs(momentum_signal) * 5, 2.0))

        for step in range(24):
            # Amplificamos ligeramente el retorno de la IA si el mercado esta en tendencia fuerte
            # Esto evita la salida de linea plana "muerta" y le da forma util
            adjusted_return = pred_returns[step] * trend_amplifier

            # Limit extreme predictions to +/- 10% movement per step vs origin
            clamped_return = max(min(adjusted_return, 0.1), -0.1)

            # Multi-horizon prediction is cumulative return from current_price
            pred_price = current_price * (1 + clamped_return)
            predicted_prices.append(float(pred_price))

            # Uncertainty bounds based on validation residuals (95% confidence interval roughly 1.96 * std)
            # Add a small base volatility to avoid 0 bounds
            horizon_vol = max(residual_std_per_horizon[step], 0.005)
            drift_bound = current_price * horizon_vol * 1.96

            lower_prices.append(float(pred_price - drift_bound))
            upper_prices.append(float(pred_price + drift_bound))

        # 4. Calcular una métrica de confianza con sentido
        # Compare model's RMSE to a naive baseline predicting the mean return
        naive_baseline = np.full_like(y_val, np.mean(y_train))
        naive_rmse = np.sqrt(mean_squared_error(y_val, naive_baseline))

        if naive_rmse > 0:
            # How much better is the model than predicting the mean return?
            improvement = (naive_rmse - best_rmse) / naive_rmse
            # Scale it to a nice 0-1 range. If improvement is negative, confidence is 0.
            # If improvement is 50%, confidence is extremely high (1.0).
            model_confidence = max(0.0, min(1.0, improvement * 2.0))

            # Boost confidence slightly if we have recent valid signals
            if current_features["signals"]["volume_pressure"] != 0:
                model_confidence = min(1.0, model_confidence + 0.1)
        else:
            model_confidence = 0.0

        current_features["signals"]["confidence"] = float(model_confidence)

        model_info = {
            "name": best_model_name,
            "version": "1.2",
            "trained_on_points": len(X),
            "last_trained_at": datetime.now().isoformat() + "Z",
            "validation_rmse": float(best_rmse)
        }

        return predicted_prices, timestamps, mode, model_info, lower_prices, upper_prices

    except Exception as e:
        import logging
        logging.error(f"Error en model.py: {e}")
        p, lower, upper = get_naive_prediction(current_price, [], 24)
        return p, timestamps, "naive", {
            "name": "FallbackNaive_Exception", "version": "1.0", "trained_on_points": 0, "last_trained_at": ""
        }, lower, upper
