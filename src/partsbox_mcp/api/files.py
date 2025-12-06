"""
Files API module.

Provides tool functions for file and image operations:
- get_image: Download a part image for display (with optional resizing)
- get_image_info: Get metadata about an image without downloading resized version
- get_image_size_estimate: Estimate dimensions and size after resizing (dry run)
- get_file: Download a file (datasheet, image, etc.)
- get_file_url: Get the download URL for a file
"""

import io
import time
from dataclasses import dataclass

import requests
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import Image
from PIL import Image as PILImage

from partsbox_mcp.client import api_client


# =============================================================================
# Constants
# =============================================================================

DEFAULT_MAX_DIMENSION = 1024  # Default max width/height in pixels
DEFAULT_JPEG_QUALITY = 85  # Default JPEG quality (1-100)
MIN_JPEG_QUALITY = 1
MAX_JPEG_QUALITY = 100
_IMAGE_CACHE_TTL = 300  # 5 minutes


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class FileUrlResponse:
    """Response for file URL retrieval."""

    success: bool
    url: str | None = None
    error: str | None = None


@dataclass
class ImageInfoResponse:
    """Response containing image metadata without the image data."""

    success: bool
    width: int | None = None
    height: int | None = None
    format: str | None = None
    file_size_bytes: int | None = None
    error: str | None = None


@dataclass
class ImageSizeEstimate:
    """Response containing estimated dimensions after resizing."""

    success: bool
    original_width: int | None = None
    original_height: int | None = None
    estimated_width: int | None = None
    estimated_height: int | None = None
    original_size_bytes: int | None = None
    estimated_size_bytes: int | None = None
    would_resize: bool = False
    format: str | None = None
    quality: int | None = None
    error: str | None = None


# =============================================================================
# Image Cache
# =============================================================================

# Cache: file_id -> (data, content_type, filename, timestamp)
_image_cache: dict[str, tuple[bytes, str | None, str | None, float]] = {}


# =============================================================================
# Internal Helper Functions
# =============================================================================


def _extract_filename(headers: dict, file_id: str, content_type: str | None) -> str | None:
    """Extract filename from headers or generate from content type."""
    content_disposition = headers.get("Content-Disposition", "")
    filename = None

    if "filename=" in content_disposition:
        # Parse filename from header like: attachment; filename="image.png"
        parts = content_disposition.split("filename=")
        if len(parts) > 1:
            filename = parts[1].strip('"\'')

    # If no filename in header, generate one from file_id and content_type
    if not filename and content_type:
        ext = content_type.split("/")[-1].split(";")[0]
        if ext in ["jpeg", "jpg", "png", "gif", "pdf", "webp"]:
            filename = f"{file_id}.{ext}"

    return filename


def _download_file_bytes(file_id: str) -> tuple[bytes, str | None, str | None]:
    """
    Download raw file bytes from PartsBox.

    Internal helper that fetches file content.

    Args:
        file_id: The file identifier (obtained from part data)

    Returns:
        Tuple of (data, content_type, filename)

    Raises:
        ToolError: If the download fails
    """
    if not file_id:
        raise ToolError("file_id is required")

    try:
        # Files are accessed via GET request to partsbox.com/files/{file_id}
        # This is a web endpoint, not the API endpoint
        url = f"https://partsbox.com/files/{file_id}"
        response = api_client._session.get(url)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type")
        filename = _extract_filename(response.headers, file_id, content_type)

        return response.content, content_type, filename
    except requests.RequestException as e:
        raise ToolError(f"Failed to download file: {e}")


def _get_cached_image(file_id: str) -> tuple[bytes, str | None, str | None] | None:
    """Retrieve cached image data if not expired."""
    if file_id in _image_cache:
        data, content_type, filename, timestamp = _image_cache[file_id]
        if time.time() - timestamp < _IMAGE_CACHE_TTL:
            return data, content_type, filename
        else:
            del _image_cache[file_id]
    return None


def _cache_image(
    file_id: str, data: bytes, content_type: str | None, filename: str | None
) -> None:
    """Cache image data with timestamp."""
    _cleanup_image_cache()
    _image_cache[file_id] = (data, content_type, filename, time.time())


def _cleanup_image_cache() -> None:
    """Remove expired cache entries."""
    now = time.time()
    expired = [k for k, v in _image_cache.items() if now - v[3] > _IMAGE_CACHE_TTL]
    for k in expired:
        del _image_cache[k]


def _download_image_cached(file_id: str) -> tuple[bytes, str | None, str | None]:
    """Download image with caching."""
    cached = _get_cached_image(file_id)
    if cached:
        return cached

    data, content_type, filename = _download_file_bytes(file_id)
    _cache_image(file_id, data, content_type, filename)
    return data, content_type, filename


def _calculate_resize_dimensions(
    original_width: int,
    original_height: int,
    max_width: int | None,
    max_height: int | None,
) -> tuple[int, int, bool]:
    """
    Calculate target dimensions preserving aspect ratio.

    Args:
        original_width: Original image width in pixels
        original_height: Original image height in pixels
        max_width: Maximum width constraint (0 to disable, None for default)
        max_height: Maximum height constraint (0 to disable, None for default)

    Returns:
        Tuple of (new_width, new_height, would_resize)
    """
    # If both are 0, disable resizing
    if max_width == 0 and max_height == 0:
        return original_width, original_height, False

    # Apply defaults
    effective_max_width = DEFAULT_MAX_DIMENSION if max_width is None else max_width
    effective_max_height = DEFAULT_MAX_DIMENSION if max_height is None else max_height

    # Handle case where one dimension is 0 (no constraint on that axis)
    if effective_max_width == 0:
        effective_max_width = original_width
    if effective_max_height == 0:
        effective_max_height = original_height

    # Check if resize needed (never upscale)
    if original_width <= effective_max_width and original_height <= effective_max_height:
        return original_width, original_height, False

    # Calculate scale factor to fit in bounding box
    width_ratio = effective_max_width / original_width
    height_ratio = effective_max_height / original_height
    scale = min(width_ratio, height_ratio)

    new_width = max(1, int(original_width * scale))
    new_height = max(1, int(original_height * scale))

    return new_width, new_height, True


def _resize_image(
    image_data: bytes,
    image_format: str,
    max_width: int | None,
    max_height: int | None,
    quality: int | None,
) -> tuple[bytes, int, int]:
    """
    Resize image data, returning new bytes and dimensions.

    Args:
        image_data: Raw image bytes
        image_format: Format string (png, jpeg, etc.)
        max_width: Maximum width (0 to disable, None for default)
        max_height: Maximum height (0 to disable, None for default)
        quality: JPEG quality (ignored for non-JPEG)

    Returns:
        Tuple of (resized_bytes, new_width, new_height)
    """
    # Load image
    img = PILImage.open(io.BytesIO(image_data))
    original_width, original_height = img.size

    # Calculate new dimensions
    new_width, new_height, should_resize = _calculate_resize_dimensions(
        original_width, original_height, max_width, max_height
    )

    if not should_resize:
        return image_data, original_width, original_height

    # Resize using high-quality Lanczos filter
    img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)

    # Save to bytes
    output = io.BytesIO()

    # Normalize format for PIL
    pil_format = image_format.upper()
    if pil_format == "JPG":
        pil_format = "JPEG"

    save_kwargs: dict = {}
    if pil_format == "JPEG":
        save_kwargs["quality"] = quality or DEFAULT_JPEG_QUALITY
        save_kwargs["optimize"] = True
        # Ensure RGB mode for JPEG (no alpha channel)
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
    elif pil_format == "PNG":
        save_kwargs["optimize"] = True

    img.save(output, format=pil_format, **save_kwargs)
    return output.getvalue(), new_width, new_height


def _estimate_compressed_size(
    original_size: int,
    original_width: int,
    original_height: int,
    new_width: int,
    new_height: int,
    image_format: str,
    quality: int | None,
) -> int:
    """
    Estimate file size after resize (approximation).

    This uses a simple ratio-based calculation. Actual size depends
    on image content and compression efficiency.
    """
    # Calculate pixel ratio
    original_pixels = original_width * original_height
    new_pixels = new_width * new_height
    pixel_ratio = new_pixels / original_pixels if original_pixels > 0 else 1.0

    # Estimate based on pixel ratio
    estimated = int(original_size * pixel_ratio)

    # Apply quality factor for JPEG
    if image_format.lower() in ("jpeg", "jpg") and quality:
        # Quality affects size roughly linearly between 50-100
        quality_factor = quality / 100
        estimated = int(estimated * quality_factor)

    return max(estimated, 100)  # Minimum 100 bytes


def _validate_quality(quality: int | None) -> None:
    """Validate quality parameter if provided."""
    if quality is not None and (quality < MIN_JPEG_QUALITY or quality > MAX_JPEG_QUALITY):
        raise ToolError(f"quality must be between {MIN_JPEG_QUALITY} and {MAX_JPEG_QUALITY}")


# =============================================================================
# Tool Functions
# =============================================================================


def get_image(
    file_id: str,
    max_width: int | None = None,
    max_height: int | None = None,
    quality: int | None = None,
) -> Image:
    """
    Download a part image for display, with optional resizing.

    Images are automatically resized to fit within a 1024x1024 bounding box
    by default to optimize for Claude Desktop display. Use max_width and/or
    max_height to override the default, or set both to 0 to disable resizing
    and get the original image.

    Args:
        file_id: The file identifier from part data (part/img-id field)
        max_width: Maximum width in pixels. Default: 1024. Set to 0 with max_height=0
                   to disable resizing.
        max_height: Maximum height in pixels. Default: 1024. Set to 0 with max_width=0
                    to disable resizing.
        quality: JPEG compression quality (1-100). Default: 85. Only applies to JPEG
                 images; ignored for PNG/GIF/WebP.

    Returns:
        Image object for rendering in Claude Desktop. The image is resized to fit
        within the specified bounding box while preserving aspect ratio. Small
        images are never upscaled.

    Raises:
        ToolError: If the file is not an image, download fails, or quality is invalid

    Example:
        # Get image with default sizing (max 1024px)
        get_image("img_resistor_10k")

        # Get smaller thumbnail
        get_image("img_resistor_10k", max_width=256, max_height=256)

        # Get original full-resolution image
        get_image("img_resistor_10k", max_width=0, max_height=0)

        # Get image with high quality JPEG
        get_image("img_resistor_10k", quality=95)
    """
    _validate_quality(quality)

    data, content_type, _ = _download_image_cached(file_id)

    # Validate that this is an image
    if not content_type or not content_type.startswith("image/"):
        raise ToolError(f"File is not an image (content-type: {content_type})")

    # Extract format from content-type (e.g., "image/png" -> "png")
    image_format = content_type.split("/")[-1].split(";")[0]

    # Resize the image
    resized_data, _, _ = _resize_image(data, image_format, max_width, max_height, quality)

    return Image(data=resized_data, format=image_format)


def get_image_info(file_id: str) -> ImageInfoResponse:
    """
    Get metadata about an image without downloading the full resized version.

    Use this to check image dimensions and size before downloading. The image
    is fetched once and cached briefly to avoid redundant downloads if you
    subsequently call get_image.

    Args:
        file_id: The file identifier from part data (part/img-id field)

    Returns:
        ImageInfoResponse with:
        - success: Whether the operation succeeded
        - width: Original image width in pixels
        - height: Original image height in pixels
        - format: Image format (png, jpeg, gif, webp)
        - file_size_bytes: Original file size in bytes
        - error: Error message if unsuccessful

    Raises:
        ToolError: If the file is not an image or download fails

    Example:
        info = get_image_info("img_resistor_10k")
        # ImageInfoResponse(success=True, width=2048, height=1536,
        #                   format='jpeg', file_size_bytes=524288)
    """
    data, content_type, _ = _download_image_cached(file_id)

    # Validate that this is an image
    if not content_type or not content_type.startswith("image/"):
        raise ToolError(f"File is not an image (content-type: {content_type})")

    # Extract format from content-type (e.g., "image/png" -> "png")
    image_format = content_type.split("/")[-1].split(";")[0]

    # Get dimensions using PIL
    img = PILImage.open(io.BytesIO(data))
    width, height = img.size

    return ImageInfoResponse(
        success=True,
        width=width,
        height=height,
        format=image_format,
        file_size_bytes=len(data),
    )


def get_image_size_estimate(
    file_id: str,
    max_width: int | None = None,
    max_height: int | None = None,
    quality: int | None = None,
) -> ImageSizeEstimate:
    """
    Estimate the dimensions and file size after resizing without returning the image.

    This is a "dry run" that predicts what get_image would return with the same
    parameters. Use this to decide if you need to adjust resize parameters before
    downloading the actual image.

    Args:
        file_id: The file identifier from part data (part/img-id field)
        max_width: Maximum width in pixels. Default: 1024.
        max_height: Maximum height in pixels. Default: 1024.
        quality: JPEG compression quality (1-100). Default: 85.

    Returns:
        ImageSizeEstimate with:
        - success: Whether the operation succeeded
        - original_width: Original image width in pixels
        - original_height: Original image height in pixels
        - estimated_width: Width after resize
        - estimated_height: Height after resize
        - original_size_bytes: Original file size in bytes
        - estimated_size_bytes: Estimated file size after resize (approximate)
        - would_resize: Whether the image would be resized
        - format: Image format
        - quality: Quality setting that would be used for JPEG
        - error: Error message if unsuccessful

    Note:
        The estimated_size_bytes is an approximation. Actual size may vary by
        10-20% depending on image content and compression efficiency.

    Raises:
        ToolError: If the file is not an image, download fails, or quality is invalid

    Example:
        estimate = get_image_size_estimate("img_resistor_10k", max_width=512)
        # ImageSizeEstimate(success=True, original_width=2048, original_height=1536,
        #                   estimated_width=512, estimated_height=384,
        #                   original_size_bytes=524288, estimated_size_bytes=65536,
        #                   would_resize=True, format='jpeg', quality=85)
    """
    _validate_quality(quality)

    data, content_type, _ = _download_image_cached(file_id)

    # Validate that this is an image
    if not content_type or not content_type.startswith("image/"):
        raise ToolError(f"File is not an image (content-type: {content_type})")

    # Extract format from content-type (e.g., "image/png" -> "png")
    image_format = content_type.split("/")[-1].split(";")[0]

    # Get original dimensions using PIL
    img = PILImage.open(io.BytesIO(data))
    original_width, original_height = img.size
    original_size = len(data)

    # Calculate estimated dimensions
    estimated_width, estimated_height, would_resize = _calculate_resize_dimensions(
        original_width, original_height, max_width, max_height
    )

    # Determine effective quality
    effective_quality = quality or DEFAULT_JPEG_QUALITY

    # Estimate compressed size
    estimated_size = _estimate_compressed_size(
        original_size,
        original_width,
        original_height,
        estimated_width,
        estimated_height,
        image_format,
        effective_quality if image_format.lower() in ("jpeg", "jpg") else None,
    )

    return ImageSizeEstimate(
        success=True,
        original_width=original_width,
        original_height=original_height,
        estimated_width=estimated_width,
        estimated_height=estimated_height,
        original_size_bytes=original_size,
        estimated_size_bytes=estimated_size,
        would_resize=would_resize,
        format=image_format,
        quality=effective_quality if image_format.lower() in ("jpeg", "jpg") else None,
    )


def get_file(file_id: str) -> bytes:
    """
    Download a file (datasheet, image, etc.) from PartsBox.

    The file_id is obtained from part data. Returns binary content
    suitable for saving to disk or further processing.

    Args:
        file_id: The file identifier from part data

    Returns:
        Raw file bytes
    """
    data, _, _ = _download_file_bytes(file_id)
    return data


def get_file_url(file_id: str) -> FileUrlResponse:
    """
    Get the download URL for a PartsBox file without downloading it.

    Use this when you need the URL for external purposes such as
    embedding in documents, sharing, or downloading via a browser.

    Args:
        file_id: The file identifier from part data

    Returns:
        FileUrlResponse with the download URL
    """
    if not file_id:
        return FileUrlResponse(success=False, error="file_id is required")

    url = f"https://partsbox.com/files/{file_id}"
    return FileUrlResponse(success=True, url=url)
