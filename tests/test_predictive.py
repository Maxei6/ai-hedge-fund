from src.agents.predictive import load_model


def test_load_predictive_model():
    model = load_model()
    assert model.weights == [0.1, 0.2, 0.3]
    assert model.bias == 0.5
    assert model.predict([1, 1, 1]) == 1.1
