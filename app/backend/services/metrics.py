from fastapi import APIRouter
from src.monitoring.metrics import MetricsRecorder

router = APIRouter(prefix="/metrics", tags=["metrics"])
metrics_recorder = MetricsRecorder()


@router.get("/")
def read_metrics():
    """Return recorded metrics."""
    return metrics_recorder.get_metrics()
