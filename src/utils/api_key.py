import os


def get_api_key_from_state(state: dict, api_key_name: str) -> str:
    """Get an API key from the state object or environment."""
    if state and state.get("metadata", {}).get("request"):
        request = state["metadata"]["request"]
        if hasattr(request, 'api_keys') and request.api_keys:
            if api_key_name in request.api_keys:
                return request.api_keys.get(api_key_name)
    return os.environ.get(api_key_name)
