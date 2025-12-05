"""
Files API module.

Provides MCP tools for file/attachment operations:
- file/download - Download a file (image, datasheet, etc.) associated with a part
- file/download-image - Download an image as base64-encoded data for direct rendering
"""

import base64
from dataclasses import dataclass

import requests

from partsbox_mcp.client import api_client

# Import FastMCP Image type for proper MCP image content responses
try:
    from fastmcp.utilities.types import Image as FastMCPImage
except ImportError:
    # Fallback for older FastMCP versions
    from fastmcp import Image as FastMCPImage  # type: ignore


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class FileDownloadResponse:
    """Response for file download operations."""

    success: bool
    data_base64: str | None = None
    content_type: str | None = None
    filename: str | None = None
    error: str | None = None


@dataclass
class ImageDownloadResponse:
    """Response for image download operations with base64 encoding."""

    success: bool
    data_base64: str | None = None
    content_type: str | None = None
    filename: str | None = None
    error: str | None = None


@dataclass
class FileUrlResponse:
    """Response for file URL retrieval operations."""

    success: bool
    url: str | None = None
    error: str | None = None


# =============================================================================
# Tool Functions
# =============================================================================


def download_file(file_id: str) -> FileDownloadResponse:
    """
    Download a file from PartsBox.

    This method returns base64-encoded binary data suitable for saving to disk or
    processing (e.g., PDFs, datasheets). The data is base64-encoded to ensure
    JSON serialization compatibility.

    For images that need to be rendered by Claude Desktop, use download_image()
    instead, which returns a FastMCP Image object for direct rendering.

    Args:
        file_id: The file identifier (obtained from part data)

    Returns:
        FileDownloadResponse with base64-encoded file data

    See Also:
        download_image: For downloading images as FastMCP Image objects for rendering
    """
    if not file_id:
        return FileDownloadResponse(success=False, error="file_id is required")

    try:
        # Files are accessed via GET request to partsbox.com/files/{file_id}
        # This is a web endpoint, not the API endpoint
        url = f"https://partsbox.com/files/{file_id}"
        response = api_client._session.get(url)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type")
        content_disposition = response.headers.get("Content-Disposition", "")

        # Extract filename from Content-Disposition header if present
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

        # Base64 encode the binary data for JSON serialization
        data_base64 = base64.b64encode(response.content).decode("utf-8")

        return FileDownloadResponse(
            success=True,
            data_base64=data_base64,
            content_type=content_type,
            filename=filename,
        )
    except requests.RequestException as e:
        return FileDownloadResponse(success=False, error=f"API request failed: {e}")


def download_image(file_id: str) -> FastMCPImage | ImageDownloadResponse:
    """
    Download an image from PartsBox for rendering in Claude Desktop.

    This method returns a FastMCP Image object that Claude Desktop can render
    directly. The image is fetched from PartsBox and returned in the proper
    MCP format for immediate display.

    Note: If you need the raw image data as base64 (e.g., to save to disk,
    embed in HTML, or process further), use download_file() instead. This
    method is specifically optimized for direct rendering in Claude Desktop.

    Args:
        file_id: The file identifier (obtained from part data, e.g., part/img-id)

    Returns:
        FastMCPImage for successful image downloads (renders in Claude Desktop)
        ImageDownloadResponse for errors

    Example:
        # Get a part and display its image
        part = get_part("part_abc123")
        if part.data and part.data.get("part/img-id"):
            # This will render the image directly in Claude Desktop
            image = download_image(part.data["part/img-id"])

    See Also:
        download_file: For downloading files as base64-encoded data, including
                      images when raw data access is needed
    """
    if not file_id:
        return ImageDownloadResponse(success=False, error="file_id is required")

    try:
        # Files are accessed via GET request to partsbox.com/files/{file_id}
        # This is a web endpoint, not the API endpoint
        url = f"https://partsbox.com/files/{file_id}"
        response = api_client._session.get(url)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type")
        content_disposition = response.headers.get("Content-Disposition", "")

        # Validate that this is an image
        if not content_type or not content_type.startswith("image/"):
            return ImageDownloadResponse(
                success=False,
                error=f"File is not an image (content-type: {content_type}). Use download_file() instead.",
            )

        # Extract filename from Content-Disposition header if present
        filename = None
        if "filename=" in content_disposition:
            # Parse filename from header like: attachment; filename="image.png"
            parts = content_disposition.split("filename=")
            if len(parts) > 1:
                filename = parts[1].strip('"\'')

        # If no filename in header, generate one from file_id and content_type
        if not filename:
            ext = content_type.split("/")[-1].split(";")[0]
            if ext in ["jpeg", "jpg", "png", "gif", "webp", "svg+xml"]:
                # Handle svg+xml case
                ext = "svg" if ext == "svg+xml" else ext
                filename = f"{file_id}.{ext}"

        # Determine format from content_type
        # FastMCP Image expects format like "png", "jpeg", etc.
        image_format = content_type.split("/")[-1].split(";")[0]
        if image_format == "svg+xml":
            image_format = "svg"

        # Return FastMCP Image object which will be rendered properly by Claude Desktop
        # The Image class handles the MCP protocol format automatically
        return FastMCPImage(
            data=response.content,
            format=image_format,
        )
    except requests.RequestException as e:
        return ImageDownloadResponse(success=False, error=f"API request failed: {e}")


def get_download_file_url(file_id: str) -> FileUrlResponse:
    """
    Get the download URL for a file in PartsBox without downloading it.

    This method returns the URL that can be used to download the file directly.
    Use this when you need the URL for external purposes (e.g., embedding in
    documentation, sharing, or downloading via browser).

    Args:
        file_id: The file identifier (obtained from part data, e.g., part/img-id)

    Returns:
        FileUrlResponse containing:
        - success: Whether the URL was generated successfully
        - url: The download URL for the file
        - error: Error message (if failed)

    Example:
        # Get a part and retrieve its image URL
        part = get_part("part_abc123")
        if part.data and part.data.get("part/img-id"):
            url_result = get_download_file_url(part.data["part/img-id"])
            if url_result.success:
                print(f"Image URL: {url_result.url}")

    See Also:
        download_file: For downloading the file content as base64-encoded data
        download_image: For downloading images for rendering in Claude Desktop
    """
    if not file_id:
        return FileUrlResponse(success=False, error="file_id is required")

    # Files are accessed via GET request to partsbox.com/files/{file_id}
    url = f"https://partsbox.com/files/{file_id}"

    return FileUrlResponse(success=True, url=url)
