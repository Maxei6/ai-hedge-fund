from unittest.mock import MagicMock, patch

from src.agents.portfolio_manager import (
    PortfolioDecision,
    PortfolioManagerOutput,
    portfolio_management_agent,
)


def minimal_state(broker):
    return {
        "messages": [],
        "data": {"portfolio": {}, "analyst_signals": {}, "tickers": ["AAPL"]},
        "metadata": {"show_reasoning": False, "broker": broker},
    }


def test_portfolio_manager_executes_orders():
    broker = MagicMock()
    state = minimal_state(broker)
    decision = PortfolioDecision(action="buy", quantity=5, confidence=1.0, reasoning="")
    output = PortfolioManagerOutput(decisions={"AAPL": decision})

    with patch("src.agents.portfolio_manager.progress.update_status"), \
         patch("src.agents.portfolio_manager.generate_trading_decision", return_value=output):
        portfolio_management_agent(state)

    broker.place_order.assert_called_once_with("AAPL", 5, "buy")
    assert state["data"]["executed_orders"]["AAPL"]["quantity"] == 5
