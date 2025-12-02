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
        # The file/download endpoint returns binary data, not JSON
        response = api_client._request_raw("file/download", {"file/id": file_id})

        content_type = response.headers.get("Content-Type")
        content_disposition = response.headers.get("Content-Disposition", "")

        # Extract filename from Content-Disposition header if present
        filename = None
        if "filename=" in content_disposition:
            # Parse filename from header like: attachment; filename="image.png"
            parts = content_disposition.split("filename=")
            if len(parts) > 1:
                filename = parts[1].strip('"\'')

        return FileDownloadResponse(
            success=True,
            data=response.content,
            content_type=content_type,
            filename=filename,
        )
    except requests.RequestException as e:
        return FileDownloadResponse(success=False, error=f"API request failed: {e}")
