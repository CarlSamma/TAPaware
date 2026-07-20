"""Tests for HYDRA surrogate model."""
from hydra.surrogate_model import SurrogateModel
from shared.models import FusedPrompt


def test_predict_output_bounds() -> None:
    model = SurrogateModel(seed=0)
    prompt = FusedPrompt(
        prompt_text="test",
        feature_vector=[0.5] * 128,
        expected_asr=0.5,
        expected_stealth=0.5,
        composition=[],
        platform_native_format="generic",
        estimated_cost_usd=0.05,
    )
    pred = model.predict(prompt)
    assert 0.0 <= pred.asr <= 1.0
    assert 0.0 <= pred.stealth <= 1.0
    assert pred.cost > 0.0
    assert pred.turns >= 1.0


def test_online_update_changes_bias() -> None:
    model = SurrogateModel(seed=0)
    before = model.biases[-1][0]
    model.update_online([0.0] * 128, {"asr": 0.9})
    after = model.biases[-1][0]
    assert after != before
