"""
Unit tests for the new Storage API methods.

Tests cover:
- change_storage_settings: Modifying storage location settings
"""

import pytest

from partsbox_mcp.api.storage import change_storage_settings


class TestChangeStorageSettings:
    """Tests for the change_storage_settings function."""

    def test_change_storage_settings_full(self, fake_api_active):
        """change_storage_settings can set full flag."""
        result = change_storage_settings(
            storage_id="loc_001",
            full=True,
        )

        assert result.success is True
        assert result.error is None

    def test_change_storage_settings_single_part(self, fake_api_active):
        """change_storage_settings can set single_part flag."""
        result = change_storage_settings(
            storage_id="loc_001",
            single_part=True,
        )

        assert result.success is True
        assert result.error is None

    def test_change_storage_settings_existing_parts_only(self, fake_api_active):
        """change_storage_settings can set existing_parts_only flag."""
        result = change_storage_settings(
            storage_id="loc_001",
            existing_parts_only=True,
        )

        assert result.success is True
        assert result.error is None

    def test_change_storage_settings_multiple(self, fake_api_active):
        """change_storage_settings can set multiple flags at once."""
        result = change_storage_settings(
            storage_id="loc_001",
            full=True,
            single_part=False,
            existing_parts_only=True,
        )

        assert result.success is True
        assert result.error is None

    def test_change_storage_settings_empty_id(self, fake_api_active):
        """change_storage_settings fails with empty storage_id."""
        result = change_storage_settings(storage_id="", full=True)

        assert result.success is False
        assert "storage_id is required" in result.error

    def test_change_storage_settings_not_found(self, fake_api_active):
        """change_storage_settings handles non-existent storage."""
        result = change_storage_settings(
            storage_id="nonexistent_storage",
            full=True,
        )

        # The fake API will return 404, but requests will raise an exception
        # which gets caught and returned as an error
        assert result.success is False
