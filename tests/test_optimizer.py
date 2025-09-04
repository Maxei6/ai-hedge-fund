import numpy as np

from src.portfolio.optimizer import mean_variance_optimization, risk_parity_optimization


def sample_signals():
    return {
        "agent1": {
            "A": {"signal": "bullish", "confidence": 60},
            "B": {"signal": "bearish", "confidence": 60},
        },
        "agent2": {
            "A": {"signal": "bullish", "confidence": 80},
            "B": {"signal": "bearish", "confidence": 80},
        },
    }


def sample_covariance():
    return np.array([[0.1, 0.05], [0.05, 0.2]])


def test_mean_variance_optimizer_signs():
    signals = sample_signals()
    cov = sample_covariance()
    tickers = ["A", "B"]
    weights = mean_variance_optimization(signals, cov, tickers)
    assert weights.index.tolist() == tickers
    assert weights["A"] > 0
    assert weights["B"] < 0
    assert abs(weights.sum() - 1) < 1e-8


def test_risk_parity_optimizer_weights():
    signals = sample_signals()
    cov = sample_covariance()
    tickers = ["A", "B"]
    weights = risk_parity_optimization(signals, cov, tickers)
    assert weights.index.tolist() == tickers
    assert weights["A"] > 0
    assert weights["B"] < 0
    assert abs(abs(weights).sum() - 1) < 1e-8
    expected = np.array([1 / np.sqrt(0.1), 1 / np.sqrt(0.2)])
    expected = expected / expected.sum()
    assert np.allclose(np.abs(weights.values), expected, atol=1e-2)

