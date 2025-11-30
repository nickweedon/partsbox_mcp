"""
Pytest configuration and fixtures for PartsBox MCP Server tests.
"""

import pytest

from tests.fake_partsbox import FakePartsBoxAPI, SAMPLE_PARTS, get_sample_parts


@pytest.fixture
def sample_parts():
    """Provide sample parts data."""
    return get_sample_parts()


@pytest.fixture
def fake_api():
    """
    Provide a fake PartsBox API context manager.

    Usage:
        def test_something(fake_api):
            with fake_api:
                # API calls will be mocked
                ...
    """
    return FakePartsBoxAPI()


@pytest.fixture
def fake_api_active(fake_api):
    """
    Provide an already-activated fake PartsBox API.

    The mock is automatically started and stopped.
    """
    with fake_api:
        yield fake_api


@pytest.fixture
def empty_api():
    """Provide a fake API with no parts."""
    return FakePartsBoxAPI(parts=[])


@pytest.fixture
def single_part_api():
    """Provide a fake API with only one part."""
    return FakePartsBoxAPI(parts=[SAMPLE_PARTS[0].copy()])
