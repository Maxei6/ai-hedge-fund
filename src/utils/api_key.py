import os
from typing import Optional

from src.config import get_alpaca_keys


def get_api_key_from_state(state: dict, api_key_name: str) -> Optional[str]:
    """Get an API key from the state object, config file, or environment."""
    if state and state.get("metadata", {}).get("request"):
        request = state["metadata"]["request"]
        if hasattr(request, 'api_keys') and request.api_keys:
            if api_key_name in request.api_keys:
                return request.api_keys.get(api_key_name)
    if api_key_name in {"APCA_API_KEY_ID", "APCA_API_SECRET_KEY"}:
        key_id, secret = get_alpaca_keys()
        return key_id if api_key_name == "APCA_API_KEY_ID" else secret
    return os.environ.get(api_key_name)
