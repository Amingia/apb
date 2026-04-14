import json
import os
import time

STORE_FILE = "app/orderbook_snapshots.json"

def save_snapshot(price, book_ticker, depth):
    """
    Saves a minimal snapshot of the current order book to local JSON.
    Maintains a limited history (e.g., last 100 snapshots).
    """
    snapshot = {
        "timestamp": int(time.time() * 1000),
        "price": price,
        "bidPrice": float(book_ticker.get("bidPrice", 0)),
        "bidQty": float(book_ticker.get("bidQty", 0)),
        "askPrice": float(book_ticker.get("askPrice", 0)),
        "askQty": float(book_ticker.get("askQty", 0)),
        # Store top 5 levels for basic depth analysis
        "bids": [[float(p), float(q)] for p, q in depth.get("bids", [])[:5]],
        "asks": [[float(p), float(q)] for p, q in depth.get("asks", [])[:5]]
    }

    snapshots = load_snapshots()
    snapshots.append(snapshot)

    # Keep only the last 100 snapshots to prevent unbounded growth
    snapshots = snapshots[-100:]

    with open(STORE_FILE, "w") as f:
        json.dump(snapshots, f)

def load_snapshots():
    """
    Loads all saved snapshots from local JSON.
    """
    if not os.path.exists(STORE_FILE):
        return []
    try:
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def get_orderbook_metrics(current_snapshot, snapshots):
    """
    Calculates order book metrics like imbalance and spread.
    Compares against historical snapshots if available, else uses proxies.
    """
    bid_qty = current_snapshot["bidQty"]
    ask_qty = current_snapshot["askQty"]

    # Order book imbalance: (Bid Qty - Ask Qty) / (Bid Qty + Ask Qty)
    # Range: [-1, 1], positive = more buy pressure, negative = more sell pressure
    imbalance = 0.0
    total_qty = bid_qty + ask_qty
    if total_qty > 0:
        imbalance = (bid_qty - ask_qty) / total_qty

    # Spread in basis points (bps)
    bid_price = current_snapshot["bidPrice"]
    ask_price = current_snapshot["askPrice"]
    spread_bps = 0.0
    mid_price = (bid_price + ask_price) / 2
    if mid_price > 0:
        spread_bps = ((ask_price - bid_price) / mid_price) * 10000

    # Volume pressure based on top 5 levels
    bids = current_snapshot.get("bids", [])
    asks = current_snapshot.get("asks", [])
    total_bid_vol = sum([q for p, q in bids])
    total_ask_vol = sum([q for p, q in asks])

    vol_pressure = 0.0
    total_vol = total_bid_vol + total_ask_vol
    if total_vol > 0:
        vol_pressure = (total_bid_vol - total_ask_vol) / total_vol

    # If we have enough snapshots, we could compare changes over time.
    # For now, returning the instantaneous metrics which serve as a good proxy.
    # Future versions can expand this logic using the loaded `snapshots`.

    return {
        "imbalance": imbalance,
        "spread_bps": spread_bps,
        "volume_pressure": vol_pressure
    }
