import os
import joblib
import numpy as np
from datetime import datetime
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

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

    # Asegurarnos de que no fallará por unpack si historical_data está vacío o mal formado
    if len(X) < 100:
        return get_naive_prediction(current_price, [], 24), timestamps, "naive", {
            "name": "FallbackNaive", "version": "1.0", "trained_on_points": 0, "last_trained_at": ""
        }

    try:
        # 1. Separar entrenamiento y validación (Split temporal para evitar leak)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # 2. Selección de modelo (compiten 2 rápidos y estables)
        models = {
            "HistGradientBoostingRegressor": HistGradientBoostingRegressor(random_state=42, max_iter=50),
            "Ridge": Ridge(alpha=1.0)
        }

        best_model_name = None
        best_model = None
        best_rmse = float('inf')

        for name, clf in models.items():
            clf.fit(X_train, y_train)
            preds = clf.predict(X_val)
            # scikit-learn 1.4+ deprecated 'squared' param, we just take the root manually
            rmse = np.sqrt(mean_squared_error(y_val, preds))
            if rmse < best_rmse:
                best_rmse = rmse
                best_model = clf
                best_model_name = name

        # Retrenar el mejor modelo con todos los datos
        best_model.fit(X, y)
        joblib.dump(best_model, MODEL_FILE)

        # 3. Predicción recursiva 24h
        predicted_prices = []
        curr_p = current_price
        curr_inputs = list(current_features["model_inputs"])

        # Factor de atenuación para estabilizar las predicciones a 24h
        decay_factor = 0.95

        for step in range(24):
            # Predecir el siguiente retorno logarítmico (o porcentual, según la etiqueta y de features.py)
            pred_val = best_model.predict([curr_inputs])[0]

            # Limitar la predicción y aplicar decaimiento hacia 0 a medida que nos alejamos
            pred_val = max(min(pred_val, 0.05), -0.05) * (decay_factor ** step)

            # Calcular siguiente precio
            next_p = curr_p * (1 + pred_val)
            predicted_prices.append(float(next_p))

            # Actualizar features básicas para el siguiente bucle
            curr_inputs[0] = pred_val # Actualizar F1 (Retorno)
            curr_inputs[1] = pred_val # Proxy para F2 (Momentum corto)
            # El resto de variables estructurales (Vols, Distancias) decaen lentamente
            for idx in [2,3,4,5]:
                curr_inputs[idx] *= 0.98

            curr_p = next_p

        # 4. Calcular una métrica de confianza más estable y seria (0 a 1)
        # Basada en la escala del RMSE respecto a la desviación estándar de la serie
        target_std = np.std(y_val) if np.std(y_val) > 0 else 1.0
        relative_error = best_rmse / target_std
        # Si el error relativo es > 1, el modelo es peor que la media (confianza 0)
        # Si es cercano a 0, confianza alta
        model_confidence = max(0.0, min(1.0, 1.0 - relative_error))

        # Sobrescribir la confianza básica proveniente de features
        current_features["signals"]["confidence"] = float(model_confidence)

        model_info = {
            "name": best_model_name,
            "version": "1.1",
            "trained_on_points": len(X),
            "last_trained_at": datetime.now().isoformat() + "Z",
            "validation_rmse": float(best_rmse)
        }

        return predicted_prices, timestamps, mode, model_info

    except Exception as e:
        # En caso de excepción real, fallback a naive
        import logging
        logging.error(f"Error en model.py: {e}")
        return get_naive_prediction(current_price, [], 24), timestamps, "naive", {
            "name": "FallbackNaive_Exception", "version": "1.0", "trained_on_points": 0, "last_trained_at": ""
        }
