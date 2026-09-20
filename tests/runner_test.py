"""tests runner.py"""

from pathlib import Path 
from unittest.mock import patch 

from sdp_control.runner import run_observation, run_processing

def test_run_observation():

	with patch("sdp_control.runner.subprocess.run") as mock_run:
		run_observation(Path("/tmp/data"), Path("/tmp/data/out.ms"))

		args = mock_run.call_args[0][0]
		assert args[0] == "docker"
		assert args[-1] == "/data/out.ms" 

def test_run_processing():

	with patch("sdp_control.runner.subprocess.run") as mock_run:
		run_processing(Path("/tmp/data"), Path("/tmp/data/out.ms"), Path("/tmp/data/out"))

		args = mock_run.call_args[0][0]
		assert args[0] == "docker"
		assert args[-2] == "/data/out.ms" 