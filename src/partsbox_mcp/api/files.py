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


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class FileDownloadResponse:
    """Response for file download operations."""

    success: bool
    data: bytes | None = None
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


# =============================================================================
# Tool Functions
# =============================================================================


def download_file(file_id: str) -> FileDownloadResponse:
    """
    Download a file from PartsBox.

    This method returns raw binary data suitable for saving to disk or processing
    in binary form (e.g., PDFs, datasheets).

    For images that need to be rendered by Claude Desktop, use download_image()
    instead, which returns base64-encoded data that can be easily saved and viewed.

    See Also:
        download_image: For downloading images as base64-encoded data for rendering
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

        return FileDownloadResponse(
            success=True,
            data=response.content,
            content_type=content_type,
            filename=filename,
        )
    except requests.RequestException as e:
        return FileDownloadResponse(success=False, error=f"API request failed: {e}")


def download_image(file_id: str) -> ImageDownloadResponse:
    """
    Download an image from PartsBox as base64-encoded data.

    This method is specifically designed for images that need to be rendered
    by Claude Desktop. Unlike download_file(), this returns base64-encoded
    data instead of raw bytes, which Claude Desktop can decode, save to a file,
    and then render directly using its view tool.

    Args:
        file_id: The file identifier (obtained from part data, e.g., part/img-id)

    Returns:
        ImageDownloadResponse containing:
        - success: Whether the download succeeded
        - data_base64: Base64-encoded image data (if successful)
        - content_type: MIME type of the image (e.g., "image/png", "image/jpeg")
        - filename: Suggested filename from server (if provided)
        - error: Error message (if failed)

    Workflow for Claude Desktop:
        1. Call download_image() to get base64-encoded image data
        2. Decode the base64 string and save to a file (e.g., /home/claude/image.png)
        3. Use the view tool to render the saved image

    Example:
        # Get a part and download its image
        part = get_part("part_abc123")
        if part.data and part.data.get("part/img-id"):
            result = download_image(part.data["part/img-id"])
            if result.success:
                # Claude Desktop can decode and save this
                import base64
                image_bytes = base64.b64decode(result.data_base64)
                with open("/home/claude/part_image.png", "wb") as f:
                    f.write(image_bytes)
                # Then use view tool to render it

    See Also:
        download_file: For downloading non-image files or when raw bytes are needed
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

        # Encode the binary data as base64
        data_base64 = base64.b64encode(response.content).decode("utf-8")

        return ImageDownloadResponse(
            success=True,
            data_base64=data_base64,
            content_type=content_type,
            filename=filename,
        )
    except requests.RequestException as e:
        return ImageDownloadResponse(success=False, error=f"API request failed: {e}")
