"""Portfolio optimization algorithms."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


def _expected_returns_from_signals(
    analyst_signals: Dict[str, Dict[str, Dict[str, float | str]]],
    tickers: List[str],
) -> np.ndarray:
    """Convert analyst signals into a vector of expected returns.

    Each agent provides a signal ("bullish"/"bearish"/"neutral") and a
    confidence level between 0 and 100. We map these into expected returns by
    summing signed confidences for each ticker and scaling to [-1, 1].
    """

    expected = []
    for ticker in tickers:
        score = 0.0
        for agent_signals in analyst_signals.values():
            ticker_signal = agent_signals.get(ticker)
            if not ticker_signal:
                continue
            signal = ticker_signal.get("signal")
            confidence = float(ticker_signal.get("confidence", 0))
            if signal == "bullish":
                score += confidence
            elif signal == "bearish":
                score -= confidence
            # neutral contributes 0
        # scale score to a more reasonable magnitude
        expected.append(score / 100)
    return np.array(expected, dtype=float)


def _prepare_covariance(covariance: np.ndarray | pd.DataFrame, tickers: List[str]) -> np.ndarray:
    """Ensure covariance matrix is a NumPy array ordered by tickers."""

    if isinstance(covariance, pd.DataFrame):
        return covariance.loc[tickers, tickers].to_numpy(dtype=float)
    return np.asarray(covariance, dtype=float)


def mean_variance_optimization(
    analyst_signals: Dict[str, Dict[str, Dict[str, float | str]]],
    covariance: np.ndarray | pd.DataFrame,
    tickers: List[str],
    risk_aversion: float = 1.0,
) -> pd.Series:
    """Compute portfolio weights using a basic mean-variance optimiser.

    The optimiser maximises ``mu^T w - risk_aversion * w^T Σ w`` subject to
    ``sum(w) = 1`` where ``mu`` are expected returns derived from analyst
    signals and ``Σ`` is the asset covariance matrix.
    """

    mu = _expected_returns_from_signals(analyst_signals, tickers)
    cov = _prepare_covariance(covariance, tickers)

    if not np.any(mu):
        return pd.Series(np.zeros(len(tickers)), index=tickers)

    inv_cov = np.linalg.pinv(cov)
    ones = np.ones(len(tickers))

    A = ones @ inv_cov @ ones
    B = ones @ inv_cov @ mu
    gamma = (B - 2 * risk_aversion) / A
    weights = 1 / (2 * risk_aversion) * inv_cov @ (mu - gamma * ones)
    return pd.Series(weights, index=tickers)


def risk_parity_optimization(
    analyst_signals: Dict[str, Dict[str, Dict[str, float | str]]],
    covariance: np.ndarray | pd.DataFrame,
    tickers: List[str],
) -> pd.Series:
    """Compute risk parity portfolio weights.

    We first compute inverse-volatility weights from the covariance matrix,
    then apply the sign of expected returns derived from analyst signals. The
    final weights are normalised such that the sum of absolute weights equals
    one. This allows for simple long/short allocations while equalising risk
    contributions across assets.
    """

    mu = _expected_returns_from_signals(analyst_signals, tickers)
    cov = _prepare_covariance(covariance, tickers)

    vols = np.sqrt(np.diag(cov))
    base = 1 / vols
    base = base / base.sum()

    signs = np.sign(mu)
    weights = base * signs

    if np.sum(np.abs(weights)) > 0:
        weights = weights / np.sum(np.abs(weights))

    return pd.Series(weights, index=tickers)
