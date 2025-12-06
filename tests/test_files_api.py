"""
Unit tests for the Files API module.

Tests cover:
- get_image: Downloading part images (with optional resizing)
- get_image_info: Getting image metadata
- get_image_size_estimate: Estimating resized image dimensions
- get_file: Downloading raw file bytes
- get_file_url: Getting file download URLs
"""

import io

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

from partsbox_mcp.api.files import (
    FileUrlResponse,
    ImageInfoResponse,
    ImageSizeEstimate,
    get_file,
    get_file_url,
    get_image,
    get_image_info,
    get_image_size_estimate,
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

    def test_get_file_matches_get_image_original_for_images(self, fake_api_active):
        """get_file returns same data as get_image when resizing is disabled."""
        # Use max_width=0 and max_height=0 to disable resizing
        image_result = get_image(file_id="img_led_red", max_width=0, max_height=0)
        file_result = get_file(file_id="img_led_red")

        # Both should have the same raw bytes when resizing is disabled
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


# =============================================================================
# Image Resizing Tests
# =============================================================================


class TestGetImageResizing:
    """Tests for the get_image function with resizing."""

    def _get_image_dimensions(self, image_data: bytes) -> tuple[int, int]:
        """Helper to get dimensions from image bytes."""
        img = PILImage.open(io.BytesIO(image_data))
        return img.size

    def test_get_image_default_resize_large_image(self, fake_api_active):
        """get_image applies default 1024px max resize to large images."""
        result = get_image(file_id="img_large_part")

        assert isinstance(result, Image)
        width, height = self._get_image_dimensions(result.data)
        # Large image (2048x1536) should be resized to fit in 1024x1024
        assert width <= 1024
        assert height <= 1024

    def test_get_image_no_resize_small_image(self, fake_api_active):
        """get_image does not resize images smaller than default max."""
        result = get_image(file_id="img_small_part")

        assert isinstance(result, Image)
        width, height = self._get_image_dimensions(result.data)
        # Small image (64x64) should not be resized
        assert width == 64
        assert height == 64

    def test_get_image_custom_dimensions(self, fake_api_active):
        """get_image respects custom max_width and max_height."""
        result = get_image(
            file_id="img_large_part",
            max_width=256,
            max_height=256,
        )

        assert isinstance(result, Image)
        width, height = self._get_image_dimensions(result.data)
        assert width <= 256
        assert height <= 256

    def test_get_image_original_size(self, fake_api_active):
        """get_image returns original when max_width=0 and max_height=0."""
        result = get_image(
            file_id="img_large_part",
            max_width=0,
            max_height=0,
        )

        assert isinstance(result, Image)
        width, height = self._get_image_dimensions(result.data)
        # Original large image is 2048x1536
        assert width == 2048
        assert height == 1536

    def test_get_image_preserves_aspect_ratio(self, fake_api_active):
        """get_image preserves aspect ratio when resizing."""
        result = get_image(
            file_id="img_wide_part",  # 1920x1080 (16:9)
            max_width=800,
            max_height=800,
        )

        assert isinstance(result, Image)
        width, height = self._get_image_dimensions(result.data)
        # Should preserve 16:9 aspect ratio
        original_ratio = 1920 / 1080
        result_ratio = width / height
        assert abs(original_ratio - result_ratio) < 0.01

    def test_get_image_no_upscale_small_image(self, fake_api_active):
        """get_image does not upscale small images."""
        result = get_image(
            file_id="img_small_part",  # 64x64
            max_width=2000,
            max_height=2000,
        )

        assert isinstance(result, Image)
        width, height = self._get_image_dimensions(result.data)
        # Should not upscale
        assert width == 64
        assert height == 64

    def test_get_image_quality_parameter_jpeg(self, fake_api_active):
        """get_image accepts quality parameter for JPEG."""
        # Get same image with different quality settings
        high_quality = get_image(
            file_id="img_large_jpeg_part",
            max_width=512,
            quality=95,
        )
        low_quality = get_image(
            file_id="img_large_jpeg_part",
            max_width=512,
            quality=30,
        )

        assert isinstance(high_quality, Image)
        assert isinstance(low_quality, Image)
        # Lower quality should generally produce smaller file
        # (not always guaranteed, but usually true)
        assert len(low_quality.data) <= len(high_quality.data) * 1.5

    def test_get_image_quality_validation_too_high(self, fake_api_active):
        """get_image validates quality range - too high."""
        with pytest.raises(ToolError) as exc_info:
            get_image(file_id="img_resistor_10k", quality=101)
        assert "quality" in str(exc_info.value).lower()

    def test_get_image_quality_validation_too_low(self, fake_api_active):
        """get_image validates quality range - too low."""
        with pytest.raises(ToolError) as exc_info:
            get_image(file_id="img_resistor_10k", quality=0)
        assert "quality" in str(exc_info.value).lower()

    def test_get_image_single_dimension_constraint(self, fake_api_active):
        """get_image handles single dimension constraint (width only)."""
        result = get_image(
            file_id="img_wide_part",  # 1920x1080
            max_width=480,
            max_height=0,  # No height constraint
        )

        assert isinstance(result, Image)
        width, height = self._get_image_dimensions(result.data)
        assert width <= 480


# =============================================================================
# Image Info Tests
# =============================================================================


class TestGetImageInfo:
    """Tests for the get_image_info function."""

    def test_get_image_info_success(self, fake_api_active):
        """get_image_info returns correct metadata."""
        result = get_image_info(file_id="img_large_part")

        assert isinstance(result, ImageInfoResponse)
        assert result.success is True
        assert result.width == 2048
        assert result.height == 1536
        assert result.format == "png"
        assert result.file_size_bytes is not None
        assert result.file_size_bytes > 0
        assert result.error is None

    def test_get_image_info_small_image(self, fake_api_active):
        """get_image_info returns correct metadata for small image."""
        result = get_image_info(file_id="img_small_part")

        assert result.success is True
        assert result.width == 64
        assert result.height == 64

    def test_get_image_info_wide_image(self, fake_api_active):
        """get_image_info returns correct metadata for wide image."""
        result = get_image_info(file_id="img_wide_part")

        assert result.success is True
        assert result.width == 1920
        assert result.height == 1080

    def test_get_image_info_jpeg(self, fake_api_active):
        """get_image_info returns correct format for JPEG."""
        result = get_image_info(file_id="img_large_jpeg_part")

        assert result.success is True
        assert result.format in ("jpeg", "jpg")

    def test_get_image_info_empty_id(self, fake_api_active):
        """get_image_info handles empty file_id."""
        with pytest.raises(ToolError) as exc_info:
            get_image_info(file_id="")
        assert "file_id is required" in str(exc_info.value)

    def test_get_image_info_non_image(self, fake_api_active):
        """get_image_info fails for non-image files."""
        with pytest.raises(ToolError) as exc_info:
            get_image_info(file_id="datasheet_123")
        assert "not an image" in str(exc_info.value)


# =============================================================================
# Image Size Estimate Tests
# =============================================================================


class TestGetImageSizeEstimate:
    """Tests for the get_image_size_estimate function."""

    def test_estimate_with_resize(self, fake_api_active):
        """get_image_size_estimate predicts resize correctly."""
        result = get_image_size_estimate(
            file_id="img_large_part",
            max_width=512,
            max_height=512,
        )

        assert isinstance(result, ImageSizeEstimate)
        assert result.success is True
        assert result.original_width == 2048
        assert result.original_height == 1536
        assert result.estimated_width is not None
        assert result.estimated_height is not None
        assert result.estimated_width <= 512
        assert result.estimated_height <= 512
        assert result.original_size_bytes is not None
        assert result.estimated_size_bytes is not None
        assert result.would_resize is True

    def test_estimate_no_resize_needed(self, fake_api_active):
        """get_image_size_estimate indicates when no resize needed."""
        result = get_image_size_estimate(
            file_id="img_small_part",  # 64x64
            max_width=2000,
            max_height=2000,
        )

        assert result.success is True
        assert result.would_resize is False
        assert result.estimated_width == result.original_width
        assert result.estimated_height == result.original_height

    def test_estimate_default_resize(self, fake_api_active):
        """get_image_size_estimate uses default 1024px max."""
        result = get_image_size_estimate(file_id="img_large_part")

        assert result.success is True
        assert result.would_resize is True
        assert result.estimated_width is not None
        assert result.estimated_height is not None
        assert result.estimated_width <= 1024
        assert result.estimated_height <= 1024

    def test_estimate_preserves_aspect_ratio(self, fake_api_active):
        """get_image_size_estimate maintains aspect ratio."""
        result = get_image_size_estimate(
            file_id="img_wide_part",  # 1920x1080 (16:9)
            max_width=800,
            max_height=800,
        )

        assert result.success is True
        assert result.original_width is not None
        assert result.original_height is not None
        original_ratio = result.original_width / result.original_height
        assert result.estimated_width is not None
        assert result.estimated_height is not None
        estimated_ratio = result.estimated_width / result.estimated_height
        assert abs(original_ratio - estimated_ratio) < 0.01

    def test_estimate_quality_for_jpeg(self, fake_api_active):
        """get_image_size_estimate reflects quality for JPEG."""
        high_quality = get_image_size_estimate(
            file_id="img_large_jpeg_part",
            max_width=512,
            quality=95,
        )
        low_quality = get_image_size_estimate(
            file_id="img_large_jpeg_part",
            max_width=512,
            quality=50,
        )

        assert high_quality.quality == 95
        assert low_quality.quality == 50

    def test_estimate_quality_none_for_png(self, fake_api_active):
        """get_image_size_estimate returns None quality for PNG."""
        result = get_image_size_estimate(
            file_id="img_large_part",  # PNG
            max_width=512,
            quality=95,  # Should be ignored for PNG
        )

        assert result.success is True
        assert result.quality is None  # PNG doesn't use quality

    def test_estimate_empty_id(self, fake_api_active):
        """get_image_size_estimate handles empty file_id."""
        with pytest.raises(ToolError) as exc_info:
            get_image_size_estimate(file_id="")
        assert "file_id is required" in str(exc_info.value)

    def test_estimate_quality_validation(self, fake_api_active):
        """get_image_size_estimate validates quality range."""
        with pytest.raises(ToolError) as exc_info:
            get_image_size_estimate(file_id="img_resistor_10k", quality=101)
        assert "quality" in str(exc_info.value).lower()

    def test_estimate_matches_actual_dimensions(self, fake_api_active):
        """get_image_size_estimate dimensions match actual get_image result."""
        estimate = get_image_size_estimate(
            file_id="img_large_part",
            max_width=300,
            max_height=300,
        )

        actual = get_image(
            file_id="img_large_part",
            max_width=300,
            max_height=300,
        )

        # Get actual dimensions
        img = PILImage.open(io.BytesIO(actual.data))
        actual_width, actual_height = img.size

        # Estimate should match actual dimensions
        assert estimate.estimated_width == actual_width
        assert estimate.estimated_height == actual_height

    def test_estimate_original_size_disabled(self, fake_api_active):
        """get_image_size_estimate with disabled resize shows original size."""
        result = get_image_size_estimate(
            file_id="img_large_part",
            max_width=0,
            max_height=0,
        )

        assert result.success is True
        assert result.would_resize is False
        assert result.estimated_width == result.original_width
        assert result.estimated_height == result.original_height
