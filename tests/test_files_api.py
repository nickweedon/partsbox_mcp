"""
Unit tests for the Files API module.

Tests cover:
- download_file: Downloading files/attachments
- download_image: Downloading images as MCP ImageContent
- get_download_file_url: Getting file download URLs
"""

import base64

import pytest
from mcp.types import ImageContent

from partsbox_mcp.api.files import download_file, download_image, get_download_file_url


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


class TestDownloadImage:
    """Tests for the download_image function."""

    def test_download_image_success(self, fake_api_active):
        """download_image successfully returns ImageContent for an image file."""
        result = download_image(file_id="img_resistor_10k")

        assert isinstance(result, ImageContent)
        assert result.type == "image"
        assert result.mimeType == "image/png"
        assert result.data is not None
        assert len(result.data) > 0

    def test_download_image_returns_valid_base64(self, fake_api_active):
        """download_image returns valid base64-encoded data in ImageContent."""
        result = download_image(file_id="img_esp32_module")

        assert isinstance(result, ImageContent)
        # Verify it's valid base64 by decoding it
        try:
            decoded = base64.b64decode(result.data)
            assert isinstance(decoded, bytes)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"ImageContent.data is not valid base64: {e}")

    def test_download_image_empty_id(self, fake_api_active):
        """download_image fails with empty file_id."""
        result = download_image(file_id="")

        # Should return ImageDownloadResponse for errors
        assert not isinstance(result, ImageContent)
        assert result.success is False
        assert "file_id is required" in result.error

    def test_download_image_non_image_file(self, fake_api_active):
        """download_image fails for non-image files."""
        result = download_image(file_id="datasheet_123")

        # Should return ImageDownloadResponse for non-image files
        assert not isinstance(result, ImageContent)
        assert result.success is False
        assert "not an image" in result.error

    def test_download_image_data_matches_download_file(self, fake_api_active):
        """download_image returns same data as download_file (just in different format)."""
        image_result = download_image(file_id="img_led_red")
        file_result = download_file(file_id="img_led_red")

        assert isinstance(image_result, ImageContent)
        assert file_result.success is True

        # Both should have the same base64-encoded data
        assert image_result.data == file_result.data_base64


class TestGetDownloadFileUrl:
    """Tests for the get_download_file_url function."""

    def test_get_download_file_url_success(self):
        """get_download_file_url returns the correct URL."""
        result = get_download_file_url(file_id="img_resistor_10k")

        assert result.success is True
        assert result.url == "https://partsbox.com/files/img_resistor_10k"
        assert result.error is None

    def test_get_download_file_url_empty_id(self):
        """get_download_file_url fails with empty file_id."""
        result = get_download_file_url(file_id="")

        assert result.success is False
        assert "file_id is required" in result.error
        assert result.url is None

    def test_get_download_file_url_with_special_chars(self):
        """get_download_file_url handles file IDs with various characters."""
        result = get_download_file_url(file_id="file_abc123_xyz")

        assert result.success is True
        assert result.url == "https://partsbox.com/files/file_abc123_xyz"
        assert result.error is None
