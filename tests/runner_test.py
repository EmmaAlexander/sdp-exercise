"""tests runner.py"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from sdp_control.runner import run_observation, run_processing


def test_run_observation():
    with patch("sdp_control.runner.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        run_observation(Path("/tmp/data"), Path("/tmp/data/out.ms"))

    args = mock_run.call_args[0][0]
    assert args[0] == "docker"
    assert "out.ms" in args[-1]


def test_run_processing():
    with patch("sdp_control.runner.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        run_processing(Path("/tmp/data"), Path("/tmp/data/out.ms"), Path("/tmp/data/out"))

    args = mock_run.call_args[0][0]
    assert args[0] == "docker"
    assert "out.ms" in args[-2]


def test_run_observation_raises_on_failure():
    with patch("sdp_control.runner.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="mock error")

        raised = False
        try:
            run_observation(Path("/tmp/data"), Path("/tmp/data/out.ms"))
        except Exception:
            raised = True

        assert raised