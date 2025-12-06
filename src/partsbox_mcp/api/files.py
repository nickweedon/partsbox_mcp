"""
Files API module.

Provides helper functions for file/attachment operations used by MCP resources:
- download_file_bytes: Download raw file bytes
- download_image_bytes: Download image bytes with content-type validation
- get_file_url: Get the download URL for a file

These functions are used by MCP resource handlers in server.py.
"""

from dataclasses import dataclass

import requests

from partsbox_mcp.client import api_client


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class RawFileData:
    """Internal response for raw file bytes used by resources."""

    data: bytes | None = None
    content_type: str | None = None
    filename: str | None = None
    error: str | None = None


# =============================================================================
# Helper Functions for Resources
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


def download_file_bytes(file_id: str) -> RawFileData:
    """
    Download raw file bytes from PartsBox.

    This is an internal helper function used by MCP resource handlers.
    It fetches the file and returns raw bytes suitable for creating
    FastMCP File or Image objects.

    Args:
        file_id: The file identifier (obtained from part data)

    Returns:
        RawFileData with raw bytes, content type, and filename
    """
    if not file_id:
        return RawFileData(error="file_id is required")

    try:
        # Files are accessed via GET request to partsbox.com/files/{file_id}
        # This is a web endpoint, not the API endpoint
        url = f"https://partsbox.com/files/{file_id}"
        response = api_client._session.get(url)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type")
        filename = _extract_filename(response.headers, file_id, content_type)

        return RawFileData(
            data=response.content,
            content_type=content_type,
            filename=filename,
        )
    except requests.RequestException as e:
        return RawFileData(error=f"API request failed: {e}")


def download_image_bytes(file_id: str) -> RawFileData:
    """
    Download image bytes from PartsBox with content-type validation.

    This is an internal helper function used by the image resource handler.
    It validates that the file is an image before returning the data.

    Args:
        file_id: The file identifier (obtained from part data, e.g., part/img-id)

    Returns:
        RawFileData with image bytes if successful, or error if not an image
    """
    result = download_file_bytes(file_id)
    if result.error:
        return result

    # Validate that this is an image
    if not result.content_type or not result.content_type.startswith("image/"):
        return RawFileData(
            error=f"File is not an image (content-type: {result.content_type})"
        )

    return result


def get_file_url(file_id: str) -> str:
    """
    Get the download URL for a file in PartsBox.

    Args:
        file_id: The file identifier (obtained from part data)

    Returns:
        The download URL for the file
    """
    return f"https://partsbox.com/files/{file_id}"
