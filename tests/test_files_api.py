"""
Unit tests for the Files API module.

Tests cover:
- get_image: Downloading part images
- get_file: Downloading raw file bytes
- get_file_url: Getting file download URLs
"""

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import Image

from partsbox_mcp.api.files import (
    FileUrlResponse,
    get_file,
    get_file_url,
    get_image,
)


class TestGetImage:
    """Tests for the get_image function."""

    def test_get_image_success(self, fake_api_active):
        """get_image successfully returns an Image object."""
        result = get_image(file_id="img_resistor_10k")

        assert isinstance(result, Image)
        assert result.data is not None
        assert len(result.data) > 0
        assert result._format == "png"

    def test_get_image_validates_content_type(self, fake_api_active):
        """get_image validates that the file is an image."""
        result = get_image(file_id="img_led_red")

        assert isinstance(result, Image)
        assert result._format in ("png", "jpeg", "jpg", "gif", "webp")

    def test_get_image_empty_id_raises_error(self, fake_api_active):
        """get_image raises ToolError with empty file_id."""
        with pytest.raises(ToolError) as exc_info:
            get_image(file_id="")

        assert "file_id is required" in str(exc_info.value)

    def test_get_image_non_image_file_raises_error(self, fake_api_active):
        """get_image raises ToolError for non-image files."""
        with pytest.raises(ToolError) as exc_info:
            get_image(file_id="datasheet_123")

        assert "not an image" in str(exc_info.value)


class TestGetFile:
    """Tests for the get_file function."""

    def test_get_file_image_success(self, fake_api_active):
        """get_file successfully downloads an image file."""
        result = get_file(file_id="img_resistor_10k")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_get_file_generic_success(self, fake_api_active):
        """get_file successfully downloads a generic file."""
        result = get_file(file_id="datasheet_123")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_get_file_empty_id_raises_error(self, fake_api_active):
        """get_file raises ToolError with empty file_id."""
        with pytest.raises(ToolError) as exc_info:
            get_file(file_id="")

        assert "file_id is required" in str(exc_info.value)

    def test_get_file_returns_raw_bytes(self, fake_api_active):
        """get_file returns raw bytes (not base64)."""
        result = get_file(file_id="img_esp32_module")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_get_file_matches_get_image_for_images(self, fake_api_active):
        """get_file returns same data as get_image for image files."""
        image_result = get_image(file_id="img_led_red")
        file_result = get_file(file_id="img_led_red")

        # Both should have the same raw bytes
        assert image_result.data == file_result


class TestGetFileUrl:
    """Tests for the get_file_url function."""

    def test_get_file_url_success(self):
        """get_file_url returns the correct URL."""
        result = get_file_url(file_id="img_resistor_10k")

        assert isinstance(result, FileUrlResponse)
        assert result.success is True
        assert result.url == "https://partsbox.com/files/img_resistor_10k"
        assert result.error is None

    def test_get_file_url_with_various_ids(self):
        """get_file_url handles various file IDs."""
        result = get_file_url(file_id="file_abc123_xyz")

        assert result.success is True
        assert result.url == "https://partsbox.com/files/file_abc123_xyz"

    def test_get_file_url_empty_string_returns_error(self):
        """get_file_url with empty string returns error response."""
        result = get_file_url(file_id="")

        assert result.success is False
        assert result.url is None
        assert result.error is not None
        assert "file_id is required" in result.error
