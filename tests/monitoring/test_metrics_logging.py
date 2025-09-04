from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.monitoring.metrics import MetricsRecorder
from app.backend.services import metrics as metrics_service


def test_metrics_logging_and_retrieval(tmp_path):
    db_file = tmp_path / "metrics.db"
    recorder = MetricsRecorder(db_path=str(db_file))
    recorder.record_trade_outcome("trade1", 100.0)
    recorder.record_execution_latency("trade1", 25.5)
    recorder.record_cumulative_return(0.05, timestamp=1.0)

    metrics = recorder.get_metrics()
    assert metrics["trades"][0]["outcome"] == 100.0
    assert metrics["latency"][0]["latency_ms"] == 25.5
    assert metrics["returns"][0]["cumulative_return"] == 0.05


def test_metrics_endpoint(tmp_path):
    db_file = tmp_path / "metrics.db"
    metrics_service.metrics_recorder = MetricsRecorder(db_path=str(db_file))
    metrics_service.metrics_recorder.record_trade_outcome("trade2", 50.0)

    app = FastAPI()
    app.include_router(metrics_service.router)
    client = TestClient(app)

    response = client.get("/metrics/")
    assert response.status_code == 200
    data = response.json()
    assert data["trades"][0]["trade_id"] == "trade2"
    assert data["trades"][0]["outcome"] == 50.0
