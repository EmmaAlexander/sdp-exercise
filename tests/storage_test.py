"""Tests for storage.py"""

from sdp_control.storage import get_directory_size, storage_available
import pytest

@pytest.mark.parametrize("current_size_bytes,threshold_bytes,expected", [
    (100, 200, True),   # under threshold
    (200, 200, False),  # exactly at threshold
    (250, 200, False),  # over threshold
])

def test_storage_available(current_size_bytes, threshold_bytes, expected):
	assert storage_available(current_size_bytes, threshold_bytes) is expected

def test_get_directory_size(tmp_path):
	(tmp_path / "a.txt").write_bytes(b"1234")
	(tmp_path / "b.txt").write_bytes(b"12345678")

	assert get_directory_size(tmp_path) == 12