import os
from typing import Optional, List, Dict

import requests

from src.config import get_alpaca_keys

ALPACA_BASE_URL = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")


def _auth_headers(api_key: Optional[str] = None, api_secret: Optional[str] = None) -> Dict[str, str]:
    """Generate authentication headers for Alpaca API."""
    cfg_key, cfg_secret = get_alpaca_keys()
    api_key = api_key or cfg_key
    api_secret = api_secret or cfg_secret
    if not api_key or not api_secret:
        raise ValueError("Alpaca API key and secret are required")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
    }


def get_account(api_key: Optional[str] = None, api_secret: Optional[str] = None, base_url: Optional[str] = None) -> Dict:
    """Retrieve account information from Alpaca."""
    url = f"{base_url or ALPACA_BASE_URL}/v2/account"
    response = requests.get(url, headers=_auth_headers(api_key, api_secret))
    if response.status_code >= 400:
        raise Exception(f"Error fetching account: {response.status_code} - {response.text}")
    return response.json()


def submit_order(
    symbol: str,
    qty: int,
    side: str,
    order_type: str = "market",
    time_in_force: str = "day",
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    base_url: Optional[str] = None,
    **kwargs,
) -> Dict:
    """Submit an order to Alpaca."""
    url = f"{base_url or ALPACA_BASE_URL}/v2/orders"
    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": order_type,
        "time_in_force": time_in_force,
        **kwargs,
    }
    response = requests.post(url, json=payload, headers=_auth_headers(api_key, api_secret))
    if response.status_code >= 400:
        raise Exception(f"Error submitting order: {response.status_code} - {response.text}")
    return response.json()


def get_order(order_id: str, api_key: Optional[str] = None, api_secret: Optional[str] = None, base_url: Optional[str] = None) -> Dict:
    """Get information about a specific order."""
    url = f"{base_url or ALPACA_BASE_URL}/v2/orders/{order_id}"
    response = requests.get(url, headers=_auth_headers(api_key, api_secret))
    if response.status_code >= 400:
        raise Exception(f"Error fetching order: {response.status_code} - {response.text}")
    return response.json()


def list_orders(
    status: str = "open",
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[Dict]:
    """List orders from Alpaca."""
    url = f"{base_url or ALPACA_BASE_URL}/v2/orders"
    params = {"status": status}
    response = requests.get(url, params=params, headers=_auth_headers(api_key, api_secret))
    if response.status_code >= 400:
        raise Exception(f"Error listing orders: {response.status_code} - {response.text}")
    return response.json()
