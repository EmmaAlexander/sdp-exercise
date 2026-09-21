"""Tests data_review for review prompts"""

from pathlib import Path

import pytest

from sdp_control.data_review import human_review
from sdp_control.models import Observation


def make_observation() -> Observation:
    """Build an Observation with an image_path set, as it would be at review time."""
    return Observation(image_path=Path("data/abc123_image"))


@pytest.mark.parametrize("user_input,expected", [
    ("continue", "continue"),
    ("reprocess", "reprocess"),
    ("c", "continue"),
    ("r", "reprocess"),
    ("Continue", "continue"),
    ("REPROCESS", "reprocess"),
])

def test_human_review_accepts_valid_input(user_input, expected, mocker):
    obs = make_observation()

    mocker.patch("builtins.input", return_value=user_input)

    assert human_review(obs) == expected

def test_human_review_reprompts_on_invalid_input_then_accepts(mocker):
    obs = make_observation()

    mock_input = mocker.patch(
        "builtins.input",
        side_effect=["banana", "r"],
    )

    assert human_review(obs) == "reprocess"
    assert mock_input.call_count == 2