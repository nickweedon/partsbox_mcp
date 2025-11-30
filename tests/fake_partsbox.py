"""
Fake PartsBox API server for testing.

This module provides:
- Sample data matching the real PartsBox API format
- A responses-based mock server for unit tests
- Fixtures for pytest
"""

import time
from typing import Any

import responses

# =============================================================================
# Sample Data - Matches Real PartsBox API Format
# =============================================================================

# Realistic part data based on real PartsBox API responses
# Format validated against actual API on 2024-01-23
SAMPLE_PARTS: list[dict[str, Any]] = [
    {
        "part/id": "part_001",
        "part/name": "10K Resistor 0805",
        "part/description": "10K Ohm 1% 0805 SMD Resistor",
        "part/type": "local",
        "part/manufacturer": "Yageo",
        "part/mpn": "RC0805FR-0710KL",
        "part/created": 1700000000000,
        "part/owner": "owner_001",
        "part/tags": ["resistor", "smd", "0805"],
        "part/stock": [
            {
                "stock/quantity": 500,
                "stock/storage-id": "loc_001",
                "stock/timestamp": 1700000000000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 0.01,
            }
        ],
    },
    {
        "part/id": "part_002",
        "part/name": "100nF Capacitor 0603",
        "part/description": "100nF 16V X7R 0603 MLCC",
        "part/type": "local",
        "part/manufacturer": "Samsung",
        "part/mpn": "CL10B104KB8NNNC",
        "part/created": 1700000100000,
        "part/owner": "owner_001",
        "part/tags": ["capacitor", "mlcc", "0603"],
        "part/stock": [
            {
                "stock/quantity": 1000,
                "stock/storage-id": "loc_002",
                "stock/timestamp": 1700000100000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 0.02,
            }
        ],
    },
    {
        "part/id": "part_003",
        "part/name": "ESP32-WROOM-32",
        "part/description": "ESP32 WiFi+BT Module",
        "part/type": "linked",
        "part/manufacturer": "Espressif",
        "part/mpn": "ESP32-WROOM-32",
        "part/created": 1700000200000,
        "part/owner": "owner_001",
        "part/linked-id": "linked_esp32",
        "part/tags": ["mcu", "wifi", "bluetooth", "module"],
        "part/stock": [
            {
                "stock/quantity": 25,
                "stock/storage-id": "loc_003",
                "stock/timestamp": 1700000200000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 3.50,
            }
        ],
    },
    {
        "part/id": "part_004",
        "part/name": "1K Resistor 0805",
        "part/description": "1K Ohm 1% 0805 SMD Resistor",
        "part/type": "local",
        "part/manufacturer": "Yageo",
        "part/mpn": "RC0805FR-071KL",
        "part/created": 1700000300000,
        "part/owner": "owner_001",
        "part/tags": ["resistor", "smd", "0805"],
        "part/stock": [
            {
                "stock/quantity": 5,
                "stock/storage-id": "loc_001",
                "stock/timestamp": 1700000300000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 0.01,
            }
        ],
    },
    {
        "part/id": "part_005",
        "part/name": "Red LED 0805",
        "part/description": "Red LED 0805 SMD",
        "part/type": "local",
        "part/manufacturer": "Everlight",
        "part/mpn": "19-217/R6C-AL1M2VY/3T",
        "part/created": 1700000400000,
        "part/owner": "owner_001",
        "part/tags": ["led", "smd", "0805", "red"],
        "part/stock": [],
    },
]


def get_sample_parts() -> list[dict[str, Any]]:
    """Return a copy of sample parts data."""
    return [p.copy() for p in SAMPLE_PARTS]


def get_sample_part(part_id: str) -> dict[str, Any] | None:
    """Return a single sample part by ID."""
    for part in SAMPLE_PARTS:
        if part["part/id"] == part_id:
            return part.copy()
    return None


# =============================================================================
# API Response Builders
# =============================================================================


def build_success_response(data: Any) -> dict[str, Any]:
    """Build a successful API response matching real PartsBox format."""
    return {
        "data": data,
        "partsbox.status/category": "ok",
        "partsbox.status/message": "OK",
    }


def build_error_response(message: str) -> dict[str, Any]:
    """Build an error API response."""
    return {
        "data": None,
        "partsbox.status/category": "status/error",
        "partsbox.status/message": message,
    }


# =============================================================================
# Mock Server Setup
# =============================================================================


class FakePartsBoxAPI:
    """
    A fake PartsBox API server using the responses library.

    Usage:
        with FakePartsBoxAPI() as fake_api:
            # Make requests to the API
            response = requests.post("https://api.partsbox.com/api/1/part/all")
    """

    BASE_URL = "https://api.partsbox.com/api/1"

    def __init__(self, parts: list[dict[str, Any]] | None = None):
        self._parts = parts if parts is not None else get_sample_parts()
        self._mock = responses.RequestsMock(assert_all_requests_are_fired=False)

    def __enter__(self) -> "FakePartsBoxAPI":
        self._mock.start()
        self._setup_endpoints()
        return self

    def __exit__(self, *args: Any) -> None:
        self._mock.stop()
        self._mock.reset()

    def _setup_endpoints(self) -> None:
        """Set up all mock endpoints."""
        # part/all endpoint
        self._mock.add(
            responses.POST,
            f"{self.BASE_URL}/part/all",
            json=build_success_response(self._parts),
            status=200,
        )

        # part/get endpoint - uses callback for dynamic response
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/part/get",
            callback=self._handle_part_get,
            content_type="application/json",
        )

    def _handle_part_get(
        self, request: Any
    ) -> tuple[int, dict[str, str], str]:
        """Handle part/get requests dynamically."""
        import json

        try:
            body = json.loads(request.body)
            part_id = body.get("part/id")

            if not part_id:
                return (
                    400,
                    {},
                    json.dumps(build_error_response("part/id is required")),
                )

            for part in self._parts:
                if part["part/id"] == part_id:
                    return (200, {}, json.dumps(build_success_response(part)))

            return (
                404,
                {},
                json.dumps(build_error_response(f"Part not found: {part_id}")),
            )
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def set_parts(self, parts: list[dict[str, Any]]) -> None:
        """Update the parts data (must be called before entering context)."""
        self._parts = parts


# =============================================================================
# Pytest Fixtures
# =============================================================================


def create_fake_api(
    parts: list[dict[str, Any]] | None = None,
) -> FakePartsBoxAPI:
    """Create a FakePartsBoxAPI instance for testing."""
    return FakePartsBoxAPI(parts)
