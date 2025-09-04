import json
from pathlib import Path
from typing import Optional, Tuple

_config_cache: dict | None = None


def _load_config() -> dict:
    """Load configuration from config.json once and cache it."""
    global _config_cache
    if _config_cache is None:
        config_path = Path(__file__).resolve().parent.parent / "config.json"
        if config_path.exists():
            with config_path.open() as f:
                _config_cache = json.load(f)
        else:
            _config_cache = {}
    return _config_cache


def get_alpaca_keys() -> Tuple[Optional[str], Optional[str]]:
    """Return Alpaca API key ID and secret from config file."""
    config = _load_config()
    alpaca_cfg = config.get("alpaca", {})
    api_key = alpaca_cfg.get("api_key_id") or None
    api_secret = alpaca_cfg.get("api_secret_key") or None
    return api_key, api_secret
