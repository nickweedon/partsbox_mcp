"""
Files API module.

Provides MCP tools for file/attachment operations:
- file/download - Download a file (image, datasheet, etc.) associated with a part
"""

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


# =============================================================================
# Tool Functions
# =============================================================================


def download_file(file_id: str) -> FileDownloadResponse:
    """Download a file from PartsBox."""
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
