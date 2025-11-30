#!/usr/bin/env python3
"""
One-time validation script to check fake data format against real PartsBox API.

This script queries the real PartsBox API and compares the response structure
with our fake data to ensure compatibility.

Usage:
    PARTSBOX_API_KEY=your_key python tests/validate_api_format.py

Note: This requires a valid API key and is meant to be run manually, not as
part of the regular test suite.
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.fake_partsbox import SAMPLE_PARTS, build_success_response


def get_api_key() -> str | None:
    """Get API key from environment."""
    load_dotenv()
    return os.getenv("PARTSBOX_API_KEY")


def fetch_real_parts(api_key: str) -> dict:
    """Fetch parts from the real PartsBox API."""
    url = "https://api.partsbox.com/api/1/part/all"
    headers = {
        "Authorization": f"APIKey {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, json={})
    response.raise_for_status()
    return response.json()


def extract_keys_recursive(obj: any, prefix: str = "") -> set[str]:
    """Extract all keys from a nested structure."""
    keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            keys.update(extract_keys_recursive(value, full_key))
    elif isinstance(obj, list) and obj:
        # Check first item
        keys.update(extract_keys_recursive(obj[0], f"{prefix}[]"))
    return keys


def compare_structure(real_data: dict, fake_data: dict) -> tuple[set, set, set]:
    """
    Compare the structure of real vs fake data.

    Returns:
        Tuple of (common_keys, only_in_real, only_in_fake)
    """
    real_keys = extract_keys_recursive(real_data)
    fake_keys = extract_keys_recursive(fake_data)

    common = real_keys & fake_keys
    only_real = real_keys - fake_keys
    only_fake = fake_keys - real_keys

    return common, only_real, only_fake


def main() -> int:
    """Run validation."""
    api_key = get_api_key()

    if not api_key:
        print("=" * 60)
        print("SKIPPED: No PARTSBOX_API_KEY found in environment")
        print("=" * 60)
        print()
        print("To validate against the real API, set your API key:")
        print("  export PARTSBOX_API_KEY=partsboxapi_...")
        print()
        print("Showing fake data structure instead:")
        print()

        # Show what our fake data looks like
        fake_response = build_success_response(SAMPLE_PARTS)
        print("Fake API Response Structure:")
        print("-" * 40)
        print(json.dumps(fake_response, indent=2, default=str)[:2000])
        if len(json.dumps(fake_response)) > 2000:
            print("... (truncated)")
        return 0

    print("=" * 60)
    print("Validating fake data against real PartsBox API")
    print("=" * 60)
    print()

    try:
        real_response = fetch_real_parts(api_key)
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch from real API: {e}")
        return 1

    # Build fake response for comparison
    fake_response = build_success_response(SAMPLE_PARTS)

    print("Real API Response Status:")
    print(f"  Category: {real_response.get('partsbox.status/category')}")
    print(f"  Message: {real_response.get('partsbox.status/message')}")
    print()

    real_parts = real_response.get("data", [])
    print(f"Real API returned {len(real_parts)} parts")
    print()

    if not real_parts:
        print("WARNING: No parts returned from real API, cannot validate structure")
        return 0

    # Compare structure of first part
    print("Comparing structure of first part:")
    print("-" * 40)

    real_first = real_parts[0] if real_parts else {}
    fake_first = SAMPLE_PARTS[0]

    common, only_real, only_fake = compare_structure(real_first, fake_first)

    print(f"Common keys: {len(common)}")
    print(f"Only in real API: {len(only_real)}")
    print(f"Only in fake data: {len(only_fake)}")
    print()

    if only_real:
        print("Keys only in real API (may need to add to fake data):")
        for key in sorted(only_real):
            print(f"  - {key}")
        print()

    if only_fake:
        print("Keys only in fake data (may need to remove):")
        for key in sorted(only_fake):
            print(f"  - {key}")
        print()

    # Show sample real part
    print("Sample real part (first one):")
    print("-" * 40)
    print(json.dumps(real_first, indent=2, default=str)[:1500])
    if len(json.dumps(real_first)) > 1500:
        print("... (truncated)")
    print()

    # Validation result
    if not only_real or all("/" not in k or k.startswith("data") for k in only_real):
        print("✓ Fake data structure is compatible with real API")
        return 0
    else:
        print("⚠ Some differences found - review keys above")
        return 0  # Not a failure, just informational


if __name__ == "__main__":
    sys.exit(main())
