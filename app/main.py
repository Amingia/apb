from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging

from app.fetcher import fetch_btcusdt_data

app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fallback response template
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
    }
}

@app.get("/api/analysis")
def get_analysis():
    """
    Returns BTCUSDT analysis data adhering to a strict JSON contract.
    """
    try:
        data = fetch_btcusdt_data()

        return {
            "price": data["price"],
            "is_training": False,
            "is_fallback": False,
            "history": {
                "timestamps": data["history"]["timestamps"],
                "prices": data["history"]["prices"]
            },
            "prediction": {
                "timestamps": [],
                "prices": []
            }
        }
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        # Always return 200 OK with the fallback contract on failure
        return JSONResponse(content=FALLBACK_RESPONSE, status_code=200)

# Serve static files for the frontend
app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
