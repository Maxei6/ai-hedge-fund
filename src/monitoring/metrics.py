import os
import sqlite3
import time
from typing import Dict, List


class MetricsRecorder:
    """Record and retrieve trade metrics."""

    def __init__(self, db_path: str = "data/metrics.db") -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS trade_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT,
                outcome REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS latency_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT,
                latency_ms REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS return_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                cumulative_return REAL
            )
            """
        )
        conn.commit()
        conn.close()

    # Recording methods
    def record_trade_outcome(self, trade_id: str, outcome: float) -> None:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO trade_metrics (trade_id, outcome) VALUES (?, ?)",
            (trade_id, outcome),
        )
        conn.commit()
        conn.close()

    def record_execution_latency(self, trade_id: str, latency_ms: float) -> None:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO latency_metrics (trade_id, latency_ms) VALUES (?, ?)",
            (trade_id, latency_ms),
        )
        conn.commit()
        conn.close()

    def record_cumulative_return(self, cumulative_return: float, timestamp: float | None = None) -> None:
        if timestamp is None:
            timestamp = time.time()
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO return_metrics (timestamp, cumulative_return) VALUES (?, ?)",
            (timestamp, cumulative_return),
        )
        conn.commit()
        conn.close()

    # Retrieval
    def get_metrics(self) -> Dict[str, List[Dict]]:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT trade_id, outcome, timestamp FROM trade_metrics")
        trades = [
            {"trade_id": t[0], "outcome": t[1], "timestamp": t[2]}
            for t in cur.fetchall()
        ]
        cur.execute("SELECT trade_id, latency_ms, timestamp FROM latency_metrics")
        latency = [
            {"trade_id": t[0], "latency_ms": t[1], "timestamp": t[2]}
            for t in cur.fetchall()
        ]
        cur.execute("SELECT timestamp, cumulative_return FROM return_metrics")
        returns = [
            {"timestamp": t[0], "cumulative_return": t[1]}
            for t in cur.fetchall()
        ]
        conn.close()
        return {"trades": trades, "latency": latency, "returns": returns}
