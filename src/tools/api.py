import datetime
import os
import pandas as pd
import requests
import time

from src.data.cache import get_cache
from src.data.models import (
    CompanyNews,
    FinancialMetrics,
    Price,
    LineItem,
    InsiderTrade,
)
from src.config import get_alpaca_keys

# Global cache instance
_cache = get_cache()


def _alpaca_headers(api_key: str | None = None, secret_key: str | None = None) -> dict:
    """Build headers for Alpaca API requests."""
    cfg_key, cfg_secret = get_alpaca_keys()
    api_key = api_key or cfg_key or os.environ.get("APCA_API_KEY_ID")
    secret_key = secret_key or cfg_secret or os.environ.get("APCA_API_SECRET_KEY")
    headers = {}
    if api_key:
        headers["APCA-API-KEY-ID"] = api_key
    if secret_key:
        headers["APCA-API-SECRET-KEY"] = secret_key
    return headers


def _make_api_request(url: str, headers: dict, method: str = "GET", json_data: dict = None, max_retries: int = 3) -> requests.Response:
    """
    Make an API request with rate limiting handling and moderate backoff.
    
    Args:
        url: The URL to request
        headers: Headers to include in the request
        method: HTTP method (GET or POST)
        json_data: JSON data for POST requests
        max_retries: Maximum number of retries (default: 3)
    
    Returns:
        requests.Response: The response object
    
    Raises:
        Exception: If the request fails with a non-429 error
    """
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        else:
            response = requests.get(url, headers=headers)
        
        if response.status_code == 429 and attempt < max_retries:
            # Linear backoff: 60s, 90s, 120s, 150s...
            delay = 60 + (30 * attempt)
            print(f"Rate limited (429). Attempt {attempt + 1}/{max_retries + 1}. Waiting {delay}s before retrying...")
            time.sleep(delay)
            continue
        
        # Return the response (whether success, other errors, or final 429)
        return response


def get_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> list[Price]:
    """Fetch price data from cache or Alpaca API."""
    cache_key = f"{ticker}_{start_date}_{end_date}"

    if cached_data := _cache.get_prices(cache_key):
        return [Price(**price) for price in cached_data]

    headers = _alpaca_headers(api_key, api_secret)
    url = (
        f"https://data.alpaca.markets/v2/stocks/{ticker}/bars"
        f"?timeframe=1Day&start={start_date}&end={end_date}"
    )
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

    data = response.json()
    bars = data.get("bars", [])
    prices = [
        Price(
            open=bar.get("o"),
            close=bar.get("c"),
            high=bar.get("h"),
            low=bar.get("l"),
            volume=bar.get("v"),
            time=bar.get("t"),
        )
        for bar in bars
    ]

    if not prices:
        return []

    _cache.set_prices(cache_key, [p.model_dump() for p in prices])
    return prices


def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from cache or Alpaca API."""
    cache_key = f"{ticker}_{period}_{end_date}_{limit}"

    if cached_data := _cache.get_financial_metrics(cache_key):
        return [FinancialMetrics(**metric) for metric in cached_data]

    headers = _alpaca_headers(api_key, api_secret)
    url = (
        f"https://data.alpaca.markets/v2/stocks/{ticker}/fundamentals"
        f"?period={period}&limit={limit}&start={end_date}"
    )
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

    data = response.json()
    fundamentals = data.get("fundamentals", []) or data.get("data", [])
    financial_metrics = []
    for item in fundamentals:
        item["ticker"] = data.get("symbol", ticker)
        financial_metrics.append(FinancialMetrics(**{k: item.get(k) for k in FinancialMetrics.model_fields}))

    if not financial_metrics:
        return []

    _cache.set_financial_metrics(cache_key, [m.model_dump() for m in financial_metrics])
    return financial_metrics


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> list[LineItem]:
    """Fetch line items using Alpaca fundamentals endpoint."""
    headers = _alpaca_headers(api_key, api_secret)
    fields = ",".join(line_items)
    url = (
        f"https://data.alpaca.markets/v2/stocks/{ticker}/fundamentals"
        f"?period={period}&limit={limit}&start={end_date}&fields={fields}"
    )
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")
    data = response.json()
    fundamentals = data.get("fundamentals", []) or data.get("data", [])
    search_results = []
    for item in fundamentals:
        item["ticker"] = data.get("symbol", ticker)
        search_results.append(LineItem(**{k: item.get(k) for k in LineItem.model_fields}))
    if not search_results:
        return []
    return search_results[:limit]


def get_insider_trades(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> list[InsiderTrade]:
    """Fetch insider trades from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"
    
    # Check cache first - simple exact match
    if cached_data := _cache.get_insider_trades(cache_key):
        return [InsiderTrade(**trade) for trade in cached_data]

    # If not in cache, fetch from API
    headers = _alpaca_headers(api_key, api_secret)
    url = (
        f"https://data.alpaca.markets/v2/stocks/{ticker}/insider_trades"
        f"?end={end_date}&limit={limit}"
    )
    if start_date:
        url += f"&start={start_date}"
    response = _make_api_request(url, headers)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")
    data = response.json()
    trades = data.get("trades", [])
    all_trades = []
    fields = InsiderTrade.model_fields.keys()
    for t in trades:
        item = {k: t.get(k) for k in fields}
        item["ticker"] = ticker
        all_trades.append(InsiderTrade(**item))
    if not all_trades:
        return []
    _cache.set_insider_trades(cache_key, [trade.model_dump() for trade in all_trades])
    return all_trades


def get_company_news(
    ticker: str,
    end_date: str,
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> list[CompanyNews]:
    """Fetch company news from cache or API."""
    # Create a cache key that includes all parameters to ensure exact matches
    cache_key = f"{ticker}_{start_date or 'none'}_{end_date}_{limit}"
    
    # Check cache first - simple exact match
    if cached_data := _cache.get_company_news(cache_key):
        return [CompanyNews(**news) for news in cached_data]

    # If not in cache, fetch from API
    headers = _alpaca_headers(api_key, api_secret)
    all_news = []
    current_end_date = end_date

    while True:
        url = (
            f"https://data.alpaca.markets/v1beta1/news?symbols={ticker}&end={current_end_date}"
            f"&limit={limit}"
        )
        if start_date:
            url += f"&start={start_date}"
        response = _make_api_request(url, headers)
        if response.status_code != 200:
            raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

        data = response.json()
        news_items = data.get("news", [])
        for n in news_items:
            item = {
                "ticker": ticker,
                "title": n.get("headline"),
                "author": n.get("author"),
                "source": n.get("source"),
                "date": n.get("created_at"),
                "url": n.get("url"),
                "sentiment": n.get("sentiment"),
            }
            all_news.append(CompanyNews(**item))

        next_token = data.get("next_page_token")
        if not next_token or len(news_items) < limit:
            break
        current_end_date = all_news[-1].date.split("T")[0]

    if not all_news:
        return []
    _cache.set_company_news(cache_key, [news.model_dump() for news in all_news])
    return all_news


def get_market_cap(
    ticker: str,
    end_date: str,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> float | None:
    """Fetch market cap from Alpaca fundamentals."""
    financial_metrics = get_financial_metrics(
        ticker,
        end_date,
        period="ttm",
        limit=1,
        api_key=api_key,
        api_secret=api_secret,
    )
    if not financial_metrics:
        return None
    return financial_metrics[0].market_cap


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(ticker: str, start_date: str, end_date: str, api_key: str = None) -> pd.DataFrame:
    prices = get_prices(ticker, start_date, end_date, api_key=api_key)
    return prices_to_df(prices)
