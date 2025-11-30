"""
PartsBox API client and caching infrastructure.

This module provides:
- PartsBoxClient: HTTP client for the PartsBox API
- PaginationCache: Client-controlled caching for pagination
- JMESPath query support
"""

import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any

import jmespath
import requests
from dotenv import load_dotenv

# Load environment variables from multiple locations
# 1. Try the current working directory first
# 2. Then try the package directory (for when running as MCP server)
# 3. Then try the user's home directory
_env_paths = [
    Path.cwd() / ".env",
    Path(__file__).parent.parent.parent.parent / ".env",  # workspace/.env
    Path.home() / ".partsbox" / ".env",
]

for _env_path in _env_paths:
    if _env_path.exists():
        load_dotenv(_env_path)
        break
else:
    # Fallback: try default load_dotenv behavior
    load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

API_KEY = os.getenv("PARTSBOX_API_KEY", "")
BASE_URL = "https://api.partsbox.com/api/1"

if not API_KEY:
    raise RuntimeError(
        "PARTSBOX_API_KEY environment variable not set. "
        "Set the API key in a .env file or pass it via environment variable."
    )


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class CacheInfo:
    """Information about a cache entry."""

    valid: bool
    total_items: int | None = None
    age_seconds: int | None = None
    expires_in_seconds: int | None = None


@dataclass
class CacheEntry:
    """A cached dataset with TTL management."""

    data: list[dict[str, Any]]
    created_at: float = field(default_factory=time)
    last_accessed: float = field(default_factory=time)
    ttl: int = 300  # 5 minutes default

    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = time()

    @property
    def is_expired(self) -> bool:
        """Check if entry has exceeded TTL since last access."""
        return time() - self.last_accessed > self.ttl

    @property
    def age_seconds(self) -> int:
        """Seconds since cache was created."""
        return int(time() - self.created_at)

    @property
    def expires_in_seconds(self) -> int:
        """Seconds until cache expires (from last access)."""
        return max(0, int(self.ttl - (time() - self.last_accessed)))


# =============================================================================
# Cache Manager
# =============================================================================


class PaginationCache:
    """Manages cached datasets with client-controlled keys."""

    def __init__(self, default_ttl: int = 300):
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl

    def create(self, data: list[dict[str, Any]]) -> str:
        """Store data and return a new cache key."""
        self._lazy_cleanup()
        key = f"pb_{uuid.uuid4().hex[:8]}"
        self._cache[key] = CacheEntry(data=data, ttl=self._default_ttl)
        return key

    def get(self, key: str) -> CacheEntry | None:
        """Retrieve cache entry, return None if missing/expired."""
        self._lazy_cleanup()
        entry = self._cache.get(key)
        if entry and not entry.is_expired:
            entry.touch()
            return entry
        # Clean up expired entry
        if key in self._cache:
            del self._cache[key]
        return None

    def get_info(self, key: str) -> CacheInfo:
        """Get information about a cache entry."""
        entry = self._cache.get(key)
        if not entry or entry.is_expired:
            return CacheInfo(valid=False)
        return CacheInfo(
            valid=True,
            total_items=len(entry.data),
            age_seconds=entry.age_seconds,
            expires_in_seconds=entry.expires_in_seconds,
        )

    def invalidate(self, key: str) -> bool:
        """Explicitly invalidate a cache entry."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def _lazy_cleanup(self) -> None:
        """Remove expired entries (called on each access)."""
        expired = [k for k, v in self._cache.items() if v.is_expired]
        for k in expired:
            del self._cache[k]


# =============================================================================
# PartsBox API Client
# =============================================================================


class PartsBoxClient:
    """HTTP client for the PartsBox API."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or API_KEY
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"APIKey {self._api_key}",
                "Content-Type": "application/json",
            }
        )

    def _request(
        self, operation: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a request to the PartsBox API."""
        url = f"{BASE_URL}/{operation}"
        response = self._session.post(url, json=data or {})
        response.raise_for_status()
        return response.json()

    def get_all_parts(self) -> list[dict[str, Any]]:
        """Fetch all parts from PartsBox."""
        result = self._request("part/all")
        return result.get("data", [])

    def get_part(self, part_id: str) -> dict[str, Any] | None:
        """Fetch a single part by ID."""
        result = self._request("part/get", {"part/id": part_id})
        return result.get("data")


# =============================================================================
# JMESPath Query Support
# =============================================================================


def apply_query(
    data: list[dict[str, Any]], expression: str
) -> tuple[Any, str | None]:
    """
    Apply a JMESPath expression to data.

    Args:
        data: The data to query
        expression: JMESPath expression

    Returns:
        Tuple of (result, error_message)
        error_message is None on success
    """
    try:
        result = jmespath.search(expression, data)
        return (result if result is not None else [], None)
    except jmespath.exceptions.JMESPathError as e:
        return ([], f"Invalid query expression: {e}")


# =============================================================================
# Global Instances
# =============================================================================

# Shared cache instance
cache = PaginationCache()

# Shared API client instance
api_client = PartsBoxClient()
