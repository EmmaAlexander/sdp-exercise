"""tests runner.py"""
import subprocess
from pathlib import Path

import pytest

from sdp_control.runner import run_observation, run_processing


def test_run_observation(mocker):
    mock_run = mocker.patch("sdp_control.runner.subprocess.run")
    mock_run.return_value = mocker.MagicMock(returncode=0)

    run_observation(
        Path("/tmp/data"),
        Path("/tmp/data/out.ms"),
    )

    args = mock_run.call_args[0][0]

    assert args[0] == "docker"
    assert args[-2] == "/scripts/generate_visibilities.sh"
    assert args[-1] == "/data/out.ms"


def test_run_processing(mocker):
    mock_run = mocker.patch("sdp_control.runner.subprocess.run")
    mock_run.return_value = mocker.MagicMock(returncode=0)

    run_processing(
        Path("/tmp/data"),
        Path("/tmp/data/out.ms"),
        Path("/tmp/data/out"),
    )

    args = mock_run.call_args[0][0]

    assert args[0] == "docker"
    assert args[-3] == "/scripts/process_visibilities.sh"
    assert args[-2] == "/data/out.ms"
    assert args[-1] == "/data/out"

    args = mock_run.call_args[0][0]

    assert args[0] == "docker"
    assert args[-3] == "/scripts/process_visibilities.sh"
    assert args[-2] == "/data/out.ms"
    assert args[-1] == "/data/out"


def test_run_observation_raises_on_failure(mocker):
    mock_run = mocker.patch("sdp_control.runner.subprocess.run")
    mock_run.return_value = mocker.MagicMock(
        returncode=1,
        stdout="",
        stderr="mock error",
    )

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        run_observation(
            Path("/tmp/data"),
            Path("/tmp/data/out.ms"),
        )

    assert exc_info.value.returncode == 1
    assert exc_info.value.output == ""
    assert exc_info.value.stderr == "mock error"