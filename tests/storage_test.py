"""Tests for storage.py"""

from sdp_control.storage import get_directory_size, storage_available

def test_storage_available():
	assert storage_available(current_size_bytes=100, threshold_bytes=200) is True

def test_storage_not_available():
	assert storage_available(current_size_bytes=200, threshold_bytes=200) is False
	assert storage_available(current_size_bytes=300, threshold_bytes=200) is False

def test_get_directory_size(tmp_path):
	(tmp_path / "a.txt").write_bytes(b"1234")
	(tmp_path / "b.txt").write_bytes(b"12345678")

	assert get_directory_size(tmp_path) == 12