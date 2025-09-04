import pytest
from unittest.mock import patch
from src.agents.risk_manager import (
    risk_management_agent,
    calculate_volatility_metrics,
    calculate_volatility_adjusted_limit,
    calculate_var_metrics,
)
from src.tools.api import prices_to_df
from src.data.models import Price


@pytest.fixture
def price_series():
    return [
        Price(open=100, close=100, high=100, low=100, volume=1000, time="2023-01-01"),
        Price(open=95, close=95, high=95, low=95, volume=1000, time="2023-01-02"),
        Price(open=102, close=102, high=102, low=102, volume=1000, time="2023-01-03"),
        Price(open=90, close=90, high=90, low=90, volume=1000, time="2023-01-04"),
        Price(open=94, close=94, high=94, low=94, volume=1000, time="2023-01-05"),
        Price(open=96, close=96, high=96, low=96, volume=1000, time="2023-01-06"),
    ]


@pytest.fixture
def state(price_series):
    portfolio = {
        "cash": 10000.0,
        "margin_requirement": 0.5,
        "margin_used": 0.0,
        "positions": {
            "AAA": {
                "long": 10,
                "short": 0,
                "long_cost_basis": 100.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
                "stop_loss_pct": 0.1,
            }
        },
        "realized_gains": {"AAA": {"long": 0.0, "short": 0.0}},
    }
    data = {
        "portfolio": portfolio,
        "tickers": ["AAA"],
        "start_date": "2023-01-01",
        "end_date": "2023-01-06",
        "analyst_signals": {},
    }
    return {"data": data, "messages": [], "metadata": {"show_reasoning": False}}


def test_var_and_stop_loss_metrics(state, price_series):
    prices_df = prices_to_df(price_series)
    daily_returns = prices_df["close"].pct_change().dropna()
    var_expected = calculate_var_metrics(daily_returns)

    vol_metrics = calculate_volatility_metrics(prices_df)
    vol_adj_pct = calculate_volatility_adjusted_limit(vol_metrics["annualized_volatility"])
    current_price = prices_df["close"].iloc[-1]
    total_value = state["data"]["portfolio"]["cash"] + current_price * 10
    position_limit = total_value * vol_adj_pct
    stop_loss_price = 100.0 * (1 - 0.1)
    potential_loss = (current_price - stop_loss_price) * 10
    remaining_limit = position_limit - current_price * 10 - potential_loss
    remaining_limit = max(0.0, remaining_limit)

    with patch("src.agents.risk_manager.get_prices", return_value=price_series), \
         patch("src.agents.risk_manager.progress.update_status"):
        result = risk_management_agent(state)

    analysis = result["data"]["analyst_signals"]["risk_management_agent"]["AAA"]

    assert analysis["risk_metrics"]["var_95"] == pytest.approx(var_expected["var_95"])
    assert analysis["risk_metrics"]["cvar_95"] == pytest.approx(var_expected["cvar_95"])
    assert analysis["stop_loss_metrics"]["stop_loss_price"] == pytest.approx(stop_loss_price)
    assert analysis["stop_loss_metrics"]["potential_loss"] == pytest.approx(potential_loss)
    assert analysis["remaining_position_limit"] == pytest.approx(remaining_limit)
