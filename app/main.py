import asyncio
from datetime import datetime
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

# Global cache to store the latest analysis result
_analysis_cache = {}

# Strict JSON fallback template for severe failures
FALLBACK_RESPONSE = {
    "price": 0,
    "is_training": False,
    "is_fallback": True,
    "last_updated": "",
    "history": {
        "timestamps": [],
        "prices": []
    },
    "prediction": {
        "timestamps": [],
        "prices": [],
        "lower_prices": [],
        "upper_prices": []
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

def run_analysis_pipeline():
    """
    Synchronous blocking function that runs the entire ML pipeline.
    """
    logger.info("Running analysis pipeline...")
    market_data = fetch_btcusdt_data()
    current_price = market_data["price"]

    save_snapshot(current_price, market_data["bookTicker"], market_data["depth"])
    snapshots = load_snapshots()
    orderbook_metrics = get_orderbook_metrics(snapshots[-1], snapshots)

    news_data = fetch_recent_news()

    current_features, historical_matrix = compute_features(
        market_data["history"]["prices"],
        market_data["history"]["volumes"],
        orderbook_metrics,
        news_data
    )

    predicted_prices, predicted_timestamps, mode, model_info, lower_prices, upper_prices = train_and_predict(
        current_price,
        current_features,
        historical_matrix,
        news_data["is_available"],
        market_data["history"]["timestamps"]
    )

    return {
        "price": current_price,
        "is_training": False,
        "is_fallback": mode == "naive",
        "last_updated": datetime.now().isoformat() + "Z",
        "history": {
            "timestamps": market_data["history"]["timestamps"],
            "prices": market_data["history"]["prices"]
        },
        "prediction": {
            "timestamps": predicted_timestamps,
            "prices": predicted_prices,
            "lower_prices": lower_prices,
            "upper_prices": upper_prices
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

async def update_analysis_cache():
    """
    Background task to continuously fetch data, train, and update the cache.
    Uses asyncio.to_thread to prevent blocking the event loop.
    """
    global _analysis_cache
    while True:
        try:
            # Run the heavy synchronous pipeline in a separate thread
            response = await asyncio.to_thread(run_analysis_pipeline)
            _analysis_cache = response
            logger.info("Analysis cache updated successfully.")
        except Exception as e:
            logger.error(f"Error updating analysis cache: {e}")
            if not _analysis_cache:
                fallback = FALLBACK_RESPONSE.copy()
                fallback["last_updated"] = datetime.now().isoformat() + "Z"
                _analysis_cache = fallback

        # Wait 60 seconds before next update
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Pre-populate cache using thread to avoid blocking the first request
    try:
        logger.info("Running initial synchronous data fetch...")
        response = await asyncio.to_thread(run_analysis_pipeline)
        _analysis_cache.update(response)
    except Exception as e:
        logger.error(f"Error during initial synchronous fetch: {e}")
        fallback = FALLBACK_RESPONSE.copy()
        fallback["last_updated"] = datetime.now().isoformat() + "Z"
        _analysis_cache.update(fallback)

    # Start the background polling task
    asyncio.create_task(update_analysis_cache())

@app.get("/api/analysis")
def get_analysis():
    """
    Returns the latest cached analysis.
    """
    if not _analysis_cache:
        fallback = FALLBACK_RESPONSE.copy()
        fallback["last_updated"] = datetime.now().isoformat() + "Z"
        return JSONResponse(content=fallback, status_code=200)
    return _analysis_cache

@app.get("/api/price")
def get_live_price():
    """
    Fast endpoint for UI to poll the live price without recalculating the model.
    Falls back to cached price if Binance API fails.
    """
    try:
        import httpx
        resp = httpx.get("https://api.binance.us/api/v3/ticker/price?symbol=BTCUSDT", timeout=3.0)
        resp.raise_for_status()
        live_price = float(resp.json()["price"])
        return {"price": live_price}
    except Exception as e:
        logger.error(f"Live price fetch failed: {e}")
        # Fallback to cached price
        cached_price = _analysis_cache.get("price", 0) if _analysis_cache else 0
        return {"price": cached_price}

# Serve static files for the frontend
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
