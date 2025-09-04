from __future__ import annotations

import json
from typing import List, Optional

import requests
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from src.graph.state import AgentState
from src.utils.api_key import get_api_key_from_state
from src.utils.llm import call_llm
from src.utils.progress import progress


class ResearchResponseModel(BaseModel):
    tickers: List[str]


ALPACA_SCREENER_URL = "https://data.alpaca.markets/v1beta1/screener/stocks/most_actives"
ALPACA_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"


def _fetch_screener_symbols(api_key: Optional[str]) -> List[str]:
    headers = {}
    if api_key:
        headers["APCA-API-KEY-ID"] = api_key
    try:
        resp = requests.get(ALPACA_SCREENER_URL, headers=headers, timeout=10)
        data = resp.json() if resp.status_code == 200 else {}
        most_actives = data.get("most_actives", [])
        return [item.get("symbol") for item in most_actives if item.get("symbol")]
    except Exception:
        return []


def _fetch_news_symbols(api_key: Optional[str]) -> List[str]:
    headers = {}
    if api_key:
        headers["APCA-API-KEY-ID"] = api_key
    try:
        resp = requests.get(ALPACA_NEWS_URL, headers=headers, params={"limit": 50}, timeout=10)
        data = resp.json() if resp.status_code == 200 else {}
        symbols: List[str] = []
        for article in data.get("news", []):
            symbols.extend(article.get("symbols", []))
        return symbols
    except Exception:
        return []


def research_analyst_agent(state: AgentState, agent_id: str = "research_analyst_agent"):
    """Generate a list of promising tickers using Alpaca screeners and news."""
    data = state.get("data", {})
    existing = set(data.get("tickers", []))
    api_key = get_api_key_from_state(state, "ALPACA_API_KEY")

    progress.update_status(agent_id, None, "Gathering market data")
    screener_symbols = _fetch_screener_symbols(api_key)
    news_symbols = _fetch_news_symbols(api_key)

    candidate_symbols = list(dict.fromkeys(screener_symbols + news_symbols))
    selected_symbols = candidate_symbols

    # Optionally ask LLM to pick the most promising symbols
    if candidate_symbols:
        try:
            progress.update_status(agent_id, None, "Selecting promising tickers")
            prompt = (
                "Given the following list of stock tickers from market screeners and news: "
                f"{candidate_symbols}. Choose up to 5 tickers that look most promising "
                "for further analysis. Return a JSON object with a list field 'tickers'."
            )
            result = call_llm(
                prompt,
                ResearchResponseModel,
                agent_name=agent_id,
                state=state,
                default_factory=lambda: ResearchResponseModel(tickers=candidate_symbols[:5]),
            )
            selected_symbols = result.tickers
        except Exception:
            selected_symbols = candidate_symbols[:5]

    # Update state with new tickers
    combined = list(existing.union(selected_symbols))
    data["tickers"] = combined
    state["data"] = data

    message = HumanMessage(content=json.dumps({"tickers": selected_symbols}), name=agent_id)
    progress.update_status(agent_id, None, "Done", analysis=", ".join(selected_symbols))
    return {"messages": [message], "data": state["data"]}
