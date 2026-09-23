"""Tests for storage.py"""

from pathlib import Path

import pytest

from sdp_control.storage import get_directory_size, storage_available


@pytest.mark.parametrize(
    "current_size_bytes,threshold_bytes,expected",
    [
        (100, 200, True),
        (200, 200, False),
        (250, 200, False),
    ],
)
def test_storage_available(
    current_size_bytes: int,
    threshold_bytes: int,
    expected: bool,
) -> None:
    assert storage_available(current_size_bytes, threshold_bytes) is expected


def test_get_directory_size(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"1234")
    (tmp_path / "b.txt").write_bytes(b"12345678")

    assert get_directory_size(tmp_path) == 12
