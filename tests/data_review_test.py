"""Tests data_review for review prompts"""

from pathlib import Path
from unittest.mock import patch 
import pytest

from sdp_control.models import Observation
from sdp_control.data_review import human_review

@pytest.mark.parametrize("user_input,expected", [
	("c","continue"),
	("continue","continue"),
	("r","reprocess"),
	("reprocess","reprocess"),
	("R","reprocess"),
	("REPROCESS","reprocess")
	])

def test_human_review_accepts_valid_input(user_input, expected):
	obs = Observation(image_path=Path("out_image.fits"))
	with patch("builtins.input", return_value=user_input):
		assert human_review(obs) == expected

def test_human_review_reprompts_invalid_input():
	obs = Observation(image_path=Path("out_image.fits"))	
	with patch("builtins.input", side_effect=["uhoh","r"]) as mock_input:
		assert human_review(obs) == "reprocess"

	assert mock_input.call_count == 2
