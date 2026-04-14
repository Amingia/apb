import requests
from datetime import datetime

def fetch_recent_news():
    """
    Fetches recent news about Bitcoin using GDELT DOC 2.0 API.
    Returns a dictionary with 'is_available', 'items_count', and 'headlines'.
    Handles errors gracefully to never break the application.
    """
    default_response = {
        "is_available": False,
        "items_count": 0,
        "headlines": []
    }

    try:
        # GDELT DOC 2.0 API
        # Querying for "Bitcoin" OR "BTC" in the last 24 hours
        # format=json
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": '("Bitcoin" OR "BTC")',
            "mode": "artlist",
            "maxrecords": 50,
            "format": "json",
            "sort": "datedesc"
        }

        resp = requests.get(url, params=params, timeout=5.0)
        resp.raise_for_status()

        # GDELT returns empty content sometimes or invalid JSON if no results
        if not resp.content:
            return default_response

        data = resp.json()
        articles = data.get("articles", [])

        if not articles:
            return default_response

        headlines = []
        for art in articles:
            title = art.get("title", "")
            if not title:
                continue

            # Basic heuristic sentiment (-1 to 1) based on tone if available, or just neutral
            # GDELT doc artlist sometimes provides tone, but we can default to 0
            # To meet the requirement, we will just assign a neutral sentiment for now
            # if we can't parse a real one, or implement a very basic keyword match.
            sentiment = 0.0
            title_lower = title.lower()
            if any(word in title_lower for word in ['surge', 'jump', 'gain', 'high', 'bull', 'adopt', 'success', 'soar']):
                sentiment = 0.5
            elif any(word in title_lower for word in ['crash', 'drop', 'fall', 'low', 'bear', 'ban', 'fail', 'plunge']):
                sentiment = -0.5

            published_at = art.get("seendate", "") # Format: YYYYMMDDTHHMMSSZ
            # Try to normalize date string if it exists
            if published_at:
                try:
                    dt = datetime.strptime(published_at, "%Y%m%dT%H%M%SZ")
                    published_at = dt.isoformat() + "Z"
                except ValueError:
                    pass

            headlines.append({
                "title": title,
                "source": art.get("domain", "Desconocido"),
                "published_at": published_at,
                "sentiment": sentiment
            })

        return {
            "is_available": len(headlines) > 0,
            "items_count": len(headlines),
            "headlines": headlines
        }

    except Exception:
        # If anything fails (timeout, json parse, network), return the safe default
        return default_response
