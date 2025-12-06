"""
Unit tests for the Files API module.

Tests cover:
- download_file_bytes: Downloading raw file bytes
- download_image_bytes: Downloading image bytes with validation
- get_file_url: Getting file download URLs
"""

import pytest

from partsbox_mcp.api.files import (
    RawFileData,
    download_file_bytes,
    download_image_bytes,
    get_file_url,
)


class TestDownloadFileBytes:
    """Tests for the download_file_bytes function."""

    def test_download_file_bytes_image_success(self, fake_api_active):
        """download_file_bytes successfully downloads an image file."""
        result = download_file_bytes(file_id="img_resistor_10k")

        assert result.error is None
        assert result.data is not None
        assert len(result.data) > 0
        assert result.content_type == "image/png"
        assert result.filename == "img_resistor_10k.png"

    def test_download_file_bytes_generic_success(self, fake_api_active):
        """download_file_bytes successfully downloads a generic file."""
        result = download_file_bytes(file_id="datasheet_123")

        assert result.error is None
        assert result.data is not None
        assert result.content_type == "application/octet-stream"
        assert result.filename == "datasheet_123.bin"

    def test_download_file_bytes_empty_id(self, fake_api_active):
        """download_file_bytes fails with empty file_id."""
        result = download_file_bytes(file_id="")

        assert result.error is not None
        assert "file_id is required" in result.error
        assert result.data is None

    def test_download_file_bytes_returns_raw_bytes(self, fake_api_active):
        """download_file_bytes returns raw bytes (not base64)."""
        result = download_file_bytes(file_id="img_esp32_module")

        assert result.error is None
        assert isinstance(result.data, bytes)
        assert len(result.data) > 0


class TestDownloadImageBytes:
    """Tests for the download_image_bytes function."""

    def test_download_image_bytes_success(self, fake_api_active):
        """download_image_bytes successfully returns image bytes."""
        result = download_image_bytes(file_id="img_resistor_10k")

        assert result.error is None
        assert isinstance(result.data, bytes)
        assert result.content_type == "image/png"
        assert len(result.data) > 0

    def test_download_image_bytes_validates_content_type(self, fake_api_active):
        """download_image_bytes validates that the file is an image."""
        result = download_image_bytes(file_id="img_led_red")

        assert result.error is None
        assert result.content_type.startswith("image/")

    def test_download_image_bytes_empty_id(self, fake_api_active):
        """download_image_bytes fails with empty file_id."""
        result = download_image_bytes(file_id="")

        assert result.error is not None
        assert "file_id is required" in result.error
        assert result.data is None

    def test_download_image_bytes_non_image_file(self, fake_api_active):
        """download_image_bytes fails for non-image files."""
        result = download_image_bytes(file_id="datasheet_123")

        assert result.error is not None
        assert "not an image" in result.error

    def test_download_image_bytes_data_matches_download_file_bytes(self, fake_api_active):
        """download_image_bytes returns same data as download_file_bytes for images."""
        image_result = download_image_bytes(file_id="img_led_red")
        file_result = download_file_bytes(file_id="img_led_red")

        assert image_result.error is None
        assert file_result.error is None

        # Both should have the same raw bytes
        assert image_result.data == file_result.data


class TestGetFileUrl:
    """Tests for the get_file_url function."""

    def test_get_file_url_success(self):
        """get_file_url returns the correct URL."""
        result = get_file_url(file_id="img_resistor_10k")

        assert result == "https://partsbox.com/files/img_resistor_10k"

    def test_get_file_url_with_various_ids(self):
        """get_file_url handles various file IDs."""
        result = get_file_url(file_id="file_abc123_xyz")

        assert result == "https://partsbox.com/files/file_abc123_xyz"

    def test_get_file_url_empty_string(self):
        """get_file_url with empty string returns URL with empty id."""
        # Note: validation happens at the resource level, not here
        result = get_file_url(file_id="")
        assert result == "https://partsbox.com/files/"
