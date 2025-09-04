import json
from dataclasses import dataclass
from pathlib import Path

MODEL_PATH = Path("models/predictive_model.json")


@dataclass
class PredictiveModel:
    weights: list[float]
    bias: float

    def predict(self, features: list[float]) -> float:
        return sum(w * x for w, x in zip(self.weights, features)) + self.bias


def load_model(path: str | Path = MODEL_PATH) -> PredictiveModel:
    """Load model parameters from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return PredictiveModel(weights=data["weights"], bias=data["bias"])
