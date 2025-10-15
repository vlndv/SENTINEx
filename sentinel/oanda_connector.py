# session_gpt_bot/oanda_connector.py

import requests

from datetime import datetime
from config import (
    OANDA_API_KEY, OANDA_ACCOUNT_ID, OANDA_DOMAIN,
    INSTRUMENT, GRANULARITY, ENABLE_LOGGING
)

# === OANDA Candles API Endpoint ===
OANDA_CANDLES_URL = f"{OANDA_DOMAIN}/v3/instruments/{INSTRUMENT}/candles"

# === HTTP Headers for OANDA Auth ===
HEADERS = {
    "Authorization": f"Bearer {OANDA_API_KEY}",
    "Content-Type": "application/json"
}

def fetch_latest_data(count: int = 50) -> list:
    """
    Fetches the latest completed candle data for the selected instrument.

    Args:
        count (int): Number of candles to retrieve (default: 50)

    Returns:
        list: A list of completed candle objects from OANDA (or empty list if failed)
    """
    # Query parameters for the API request
    params = {
        "granularity": GRANULARITY,    # e.g., "M15"
        "count": count,                # Number of candles to fetch
        "price": "M"                   # Use midpoint pricing for cleaner analysis
    }

    try:
        # Make GET request to OANDA candle endpoint
        response = requests.get(OANDA_CANDLES_URL, headers=HEADERS, params=params)
        response.raise_for_status()  # Raise an error for non-200 status codes

        data = response.json()
        candles = data.get("candles", [])

        # Filter to keep only fully completed candles (ignore in-progress ones)
        complete_candles = [c for c in candles if c.get("complete")]

        if ENABLE_LOGGING:
            print(f"✅ Retrieved {len(complete_candles)} complete candles.")

        return complete_candles

    except requests.RequestException as e:
        # Handle network or API errors
        if ENABLE_LOGGING:
            print(f"❌ OANDA API Request Failed: {str(e)}")
        return []
