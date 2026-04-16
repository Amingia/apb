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

        # 2. Selección de modelo (compiten Ridge y ExtraTreesRegressor)
        models = {
            "Ridge": Ridge(alpha=1.0),
            "ExtraTrees": MultiOutputRegressor(ExtraTreesRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1))
        }

        best_model_name = None
        best_model = None
        best_rmse = float('inf')
        validation_residuals = None

        for name, clf in models.items():
            clf.fit(X_train, y_train)
            preds = clf.predict(X_val)

            # RMSE Global a través de los 24 horizontes
            rmse = np.sqrt(mean_squared_error(y_val, preds))
            if rmse < best_rmse:
                best_rmse = rmse
                best_model = clf
                best_model_name = name
                validation_residuals = y_val - preds

        # Calcular desviación estándar de los residuos por horizonte
        # Esto es clave para unas bandas que tengan sentido matemático real
        residual_std_per_horizon = np.std(validation_residuals, axis=0)

        # Retrenar el mejor modelo con todos los datos disponibles
        y_full = np.array(y)
        best_model.fit(X, y_full)
        joblib.dump(best_model, MODEL_FILE)

        # 3. Predicción multi-horizonte directa y calibración de bandas
        curr_inputs = np.array(list(current_features["model_inputs"])).reshape(1, -1)
        pred_returns = best_model.predict(curr_inputs)[0]

        predicted_prices = []
        lower_prices = []
        upper_prices = []

        # Incorporamos las noticias internamente para empujar sutilmente la predicción
        sentiment_shift = 0.0
        if news_available:
            sentiment_val = current_features["signals"]["news_sentiment"]
            # Maximo de +-0.5% shift por culpa de noticias extremas
            sentiment_shift = np.sign(sentiment_val) * min(abs(sentiment_val) * 0.005, 0.005)

        for step in range(24):
            # Retorno base predicho por el modelo para este horizonte + impacto de noticias
            base_return = pred_returns[step] + sentiment_shift

            # Limitar predicciones extremas a +/- 15% de movimiento por paso vs origen para estabilidad
            clamped_return = max(min(base_return, 0.15), -0.15)

            # El precio predicho es el precio actual alterado por el retorno acumulado predicho
            pred_price = current_price * (1 + clamped_return)
            predicted_prices.append(float(pred_price))

            # Bandas de incertidumbre basadas en el residuo real de validación de este horizonte
            # Z-score 1.64 para un ~90% confidence interval
            # horizon_vol nunca será menor de 0.005 (0.5%) para asegurar que la banda es visible
            horizon_vol = max(residual_std_per_horizon[step], 0.005)

            # Escenario bajista (lower) y alcista (upper)
            drift_bound_lower = current_price * (horizon_vol * 1.64)
            drift_bound_upper = current_price * (horizon_vol * 1.64)

            lower_prices.append(float(pred_price - drift_bound_lower))
            upper_prices.append(float(pred_price + drift_bound_upper))

        # 4. Auditoría frente a baselines y cálculo estricto de confianza (0 a 100)
        # Baseline 1: Drift Medio Reciente
        drift_baseline = np.full_like(y_val, np.mean(y_train))
        drift_rmse = np.sqrt(mean_squared_error(y_val, drift_baseline))

        # Baseline 2: Último valor conocido (retorno 0 en todos los horizontes)
        zero_baseline = np.zeros_like(y_val)
        zero_rmse = np.sqrt(mean_squared_error(y_val, zero_baseline))

        best_baseline_rmse = min(drift_rmse, zero_rmse)

        if best_baseline_rmse > 0:
            # Porcentaje de mejora frente al MEJOR baseline
            improvement = (best_baseline_rmse - best_rmse) / best_baseline_rmse

            if improvement <= 0:
                # Si el modelo es peor que un baseline simple, confianza mínima por supervivencia técnica
                confidence_pct = 15.0
            else:
                # Escalamos la mejora. Una mejora del 5% frente al baseline ya es muy decente en mercados eficientes.
                # Una mejora >15% merecerá casi 100 de confianza.
                confidence_pct = min(100.0, 30.0 + (improvement * 400.0))

            # Bonus penalización por amplitud de las bandas (bandas muy anchas = menos confianza)
            avg_band_width = np.mean([u - l for u, l in zip(upper_prices, lower_prices)]) / current_price
            if avg_band_width > 0.05: # Si la banda media es mayor al 5% del precio
                confidence_pct *= 0.8
        else:
            confidence_pct = 10.0

        current_features["signals"]["confidence"] = float(max(0.0, min(100.0, confidence_pct)))

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
