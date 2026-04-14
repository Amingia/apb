from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging

from app.fetcher import fetch_btcusdt_data
from app.news import fetch_recent_news
from app.orderbook_store import save_snapshot, load_snapshots, get_orderbook_metrics
from app.features import compute_features
from app.model import train_and_predict

app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Strict JSON fallback template for severe failures
FALLBACK_RESPONSE = {
    "price": 0,
    "is_training": False,
    "is_fallback": True,
    "history": {
        "timestamps": [],
        "prices": []
    },
    "prediction": {
        "timestamps": [],
        "prices": []
    },
    "signals": {
        "news_sentiment": 0.0,
        "headline_count": 0,
        "market_regime": "neutral",
        "order_book_imbalance": 0.0,
        "spread_bps": 0.0,
        "volume_pressure": 0.0,
        "confidence": 0.0
    },
    "news": {
        "is_available": False,
        "items_count": 0,
        "headlines": []
    },
    "model": {
        "name": "HistGradientBoostingRegressor",
        "mode": "naive",
        "version": "1.0",
        "trained_on_points": 0,
        "last_trained_at": ""
    }
}

@app.get("/api/analysis")
def get_analysis():
    """
    Orchestrates market data, news, features, and model to return a strict JSON contract.
    """
    try:
        # 1. Fetch market data
        market_data = fetch_btcusdt_data()
        current_price = market_data["price"]

        # 2. Save order book snapshot and calculate metrics
        save_snapshot(current_price, market_data["bookTicker"], market_data["depth"])
        snapshots = load_snapshots()
        orderbook_metrics = get_orderbook_metrics(snapshots[-1], snapshots)

        # 3. Fetch news
        news_data = fetch_recent_news()

        # 4. Compute features
        current_features, historical_matrix = compute_features(
            market_data["history"]["prices"],
            market_data["history"]["volumes"],
            orderbook_metrics,
            news_data
        )

        # 5. Train model and predict
        predicted_prices, predicted_timestamps, mode, model_info = train_and_predict(
            current_price,
            current_features,
            historical_matrix,
            news_data["is_available"],
            market_data["history"]["timestamps"]
        )

        # 6. Construct response respecting strict JSON contract
        response = {
            "price": current_price,
            "is_training": False,
            "is_fallback": mode == "naive",
            "history": {
                "timestamps": market_data["history"]["timestamps"],
                "prices": market_data["history"]["prices"]
            },
            "prediction": {
                "timestamps": predicted_timestamps,
                "prices": predicted_prices
            },
            "signals": current_features["signals"],
            "news": news_data,
            "model": {
                "name": model_info["name"],
                "mode": mode,
                "version": model_info["version"],
                "trained_on_points": model_info["trained_on_points"],
                "last_trained_at": model_info["last_trained_at"]
            }
        }
        return response

    except Exception as e:
        logger.error(f"Error generating analysis: {e}")
        # Always return 200 OK with the fallback contract on severe failure
        return JSONResponse(content=FALLBACK_RESPONSE, status_code=200)

# Serve static files for the frontend
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
