import httpx

def fetch_btcusdt_data():
    """
    Fetches market data for BTCUSDT from Binance's public API.
    Includes current price, 90 days of 1h candles, 24h ticker, depth, and bookTicker.
    Raises exceptions on failure.
    Returns:
        dict: containing 'price', 'history' (90 days), 'ticker_24h', 'depth', 'bookTicker'.
    """
    with httpx.Client(timeout=10.0) as client:
        # Fetch current price
        price_resp = client.get("https://api.binance.us/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        price_resp.raise_for_status()
        current_price = float(price_resp.json()["price"])

        # Fetch 24h ticker
        ticker_resp = client.get("https://api.binance.us/api/v3/ticker/24hr", params={"symbol": "BTCUSDT"})
        ticker_resp.raise_for_status()
        ticker_24h = ticker_resp.json()

        # Fetch bookTicker (best bid/ask)
        book_resp = client.get("https://api.binance.us/api/v3/ticker/bookTicker", params={"symbol": "BTCUSDT"})
        book_resp.raise_for_status()
        book_ticker = book_resp.json()

        # Fetch depth (order book, limited to 50 levels for speed)
        depth_resp = client.get("https://api.binance.us/api/v3/depth", params={"symbol": "BTCUSDT", "limit": 50})
        depth_resp.raise_for_status()
        depth = depth_resp.json()

        # Fetch 90 days of 1h candles
        # 90 days * 24 hours = 2160 candles. Binance limits to 1000 per request.
        # We need to make multiple requests backwards in time, or just get the last 1000 for now and loop if needed.
        # Let's do a loop to get all 2160.
        timestamps = []
        prices = []
        volumes = [] # We might need volume for features
        klines = []

        # Start with the most recent 1000
        limit = 1000
        total_needed = 2160
        end_time = None

        while len(klines) < total_needed:
            params = {
                "symbol": "BTCUSDT",
                "interval": "1h",
                "limit": min(limit, total_needed - len(klines))
            }
            if end_time:
                params["endTime"] = end_time

            klines_resp = client.get("https://api.binance.us/api/v3/klines", params=params)
            klines_resp.raise_for_status()
            batch = klines_resp.json()

            if not batch:
                break

            # Prepend the batch since we are moving backwards in time
            klines = batch + klines
            # The earliest time in this batch is at index 0, subtract 1 ms to avoid overlap
            end_time = batch[0][0] - 1

        for kline in klines:
            timestamps.append(kline[0])
            prices.append(float(kline[4])) # Close price
            volumes.append(float(kline[5])) # Volume

        return {
            "price": current_price,
            "ticker_24h": ticker_24h,
            "bookTicker": book_ticker,
            "depth": depth,
            "history": {
                "timestamps": timestamps,
                "prices": prices,
                "volumes": volumes
            }
        }
