"""
Unit tests for the Files API module.

Tests cover:
- download_file: Downloading files/attachments
"""

import pytest

from partsbox_mcp.api.files import download_file


class TestDownloadFile:
    """Tests for the download_file function."""

    def test_download_file_image_success(self, fake_api_active):
        """download_file successfully downloads an image file."""
        result = download_file(file_id="img_resistor_10k")

        assert result.success is True
        assert result.data is not None
        assert len(result.data) > 0
        assert result.content_type == "image/png"
        assert result.filename == "img_resistor_10k.png"
        assert result.error is None

    def test_download_file_generic_success(self, fake_api_active):
        """download_file successfully downloads a generic file."""
        result = download_file(file_id="datasheet_123")

        assert result.success is True
        assert result.data is not None
        assert result.content_type == "application/octet-stream"
        assert result.filename == "datasheet_123.bin"
        assert result.error is None

    def test_download_file_empty_id(self, fake_api_active):
        """download_file fails with empty file_id."""
        result = download_file(file_id="")

        assert result.success is False
        assert "file_id is required" in result.error
        assert result.data is None

    def test_download_file_returns_binary_data(self, fake_api_active):
        """download_file returns bytes for the file content."""
        result = download_file(file_id="img_esp32_module")

        assert result.success is True
        assert isinstance(result.data, bytes)
