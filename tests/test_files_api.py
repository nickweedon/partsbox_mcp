"""
Unit tests for the Files API module.

Tests cover:
- download_file: Downloading files/attachments
"""

import base64

import pytest

from partsbox_mcp.api.files import download_file


class TestDownloadFile:
    """Tests for the download_file function."""

    def test_download_file_image_success(self, fake_api_active):
        """download_file successfully downloads an image file."""
        result = download_file(file_id="img_resistor_10k")

        assert result.success is True
        assert result.data_base64 is not None
        assert len(result.data_base64) > 0
        assert result.content_type == "image/png"
        assert result.filename == "img_resistor_10k.png"
        assert result.error is None

    def test_download_file_generic_success(self, fake_api_active):
        """download_file successfully downloads a generic file."""
        result = download_file(file_id="datasheet_123")

        assert result.success is True
        assert result.data_base64 is not None
        assert result.content_type == "application/octet-stream"
        assert result.filename == "datasheet_123.bin"
        assert result.error is None

    def test_download_file_empty_id(self, fake_api_active):
        """download_file fails with empty file_id."""
        result = download_file(file_id="")

        assert result.success is False
        assert "file_id is required" in result.error
        assert result.data_base64 is None

    def test_download_file_returns_base64_encoded_data(self, fake_api_active):
        """download_file returns base64-encoded string for the file content."""
        result = download_file(file_id="img_esp32_module")

        assert result.success is True
        assert isinstance(result.data_base64, str)

        # Verify it's valid base64 by decoding it
        try:
            decoded = base64.b64decode(result.data_base64)
            assert isinstance(decoded, bytes)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"data_base64 is not valid base64: {e}")

    def test_download_file_base64_can_be_decoded(self, fake_api_active):
        """download_file returns base64 data that can be decoded back to original bytes."""
        result = download_file(file_id="img_resistor_10k")

        assert result.success is True
        assert result.data_base64 is not None

        # Decode the base64 data
        decoded_data = base64.b64decode(result.data_base64)

        # Should be valid bytes
        assert isinstance(decoded_data, bytes)
        assert len(decoded_data) > 0
