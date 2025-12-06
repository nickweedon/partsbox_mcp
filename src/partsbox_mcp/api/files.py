"""
Files API module.

Provides tool functions for file and image operations:
- get_image: Download a part image for display
- get_file: Download a file (datasheet, image, etc.)
- get_file_url: Get the download URL for a file
"""

from dataclasses import dataclass

import requests
from fastmcp.exceptions import ToolError
from fastmcp.utilities.types import Image

from partsbox_mcp.client import api_client


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class FileUrlResponse:
    """Response for file URL retrieval."""

    success: bool
    url: str | None = None
    error: str | None = None


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


# =============================================================================
# Tool Functions
# =============================================================================


def get_image(file_id: str) -> Image:
    """
    Download a part image for display.

    The file_id is obtained from part data (e.g., the part/img-id field).
    Returns the image in a format suitable for display in Claude Desktop.

    Args:
        file_id: The file identifier from part data (part/img-id field)

    Returns:
        Image object for rendering in Claude Desktop

    Raises:
        ToolError: If the file is not an image or download fails
    """
    data, content_type, _ = _download_file_bytes(file_id)

    # Validate that this is an image
    if not content_type or not content_type.startswith("image/"):
        raise ToolError(f"File is not an image (content-type: {content_type})")

    # Extract format from content-type (e.g., "image/png" -> "png")
    image_format = content_type.split("/")[-1].split(";")[0]

    return Image(data=data, format=image_format)


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
