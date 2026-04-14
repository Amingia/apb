import httpx

def fetch_btcusdt_data():
    """
    Fetches the current price and historical data (120 1h candles) for BTCUSDT
    from Binance's public API.
    Raises exceptions on failure.
    Returns:
        dict: containing 'price' (float) and 'history' (dict with 'timestamps' and 'prices' lists).
    """
    # Use httpx to make synchronous requests to Binance
    with httpx.Client(timeout=10.0) as client:
        # Fetch current price
        # Using ticker/price endpoint to get the latest price for a symbol
        # Fallback to binance.us if binance.com is restricted
        price_resp = client.get("https://api.binance.us/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        price_resp.raise_for_status()
        price_data = price_resp.json()
        current_price = float(price_data["price"])

        # Fetch 120 1h candles
        # Using klines endpoint
        klines_resp = client.get(
            "https://api.binance.us/api/v3/klines",
            params={
                "symbol": "BTCUSDT",
                "interval": "1h",
                "limit": 120
            }
        )
        klines_resp.raise_for_status()
        klines_data = klines_resp.json()

        timestamps = []
        prices = []
        for kline in klines_data:
            # kline format:
            # [
            #   0: Open time
            #   1: Open
            #   2: High
            #   3: Low
            #   4: Close
            #   5: Volume
            #   6: Close time
            #   7: Quote asset volume
            #   8: Number of trades
            #   9: Taker buy base asset volume
            #  10: Taker buy quote asset volume
            #  11: Ignore.
            # ]
            timestamps.append(kline[0])
            prices.append(float(kline[4]))

        return {
            "price": current_price,
            "history": {
                "timestamps": timestamps,
                "prices": prices
            }
        }
