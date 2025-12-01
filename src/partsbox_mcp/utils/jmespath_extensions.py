"""
Custom JMESPath functions for enhanced query capabilities.

This module provides custom JMESPath functions to enable:
- regex_replace(): Text transformation via regex find-and-replace
- int(): String to integer conversion with safe null handling
- str(): Convert any value to string
- nvl(): Provide default value when expression is null (like Oracle NVL)

These functions enable LLMs to construct queries that transform and filter
component values like "100 ohm" → 100 for numeric range comparisons.

The nvl() function is particularly important for safely handling nullable fields
in PartsBox data, preventing errors like:
    "In function contains(), invalid type for value: None"

Example safe query using nvl():
    [?contains(nvl("part/name", ''), 'resistor')]
"""

import re
import jmespath
from jmespath import functions
from typing import Any, Optional, Union


class CustomFunctions(functions.Functions):
    """Custom JMESPath functions for PartsBox MCP server."""

    @functions.signature(
        {'types': ['string']},
        {'types': ['string']},
        {'types': ['string', 'null']}
    )
    def _func_regex_replace(
        self,
        pattern: str,
        replacement: str,
        value: Optional[str]
    ) -> Optional[str]:
        """
        Perform regex find-and-replace on a string (like sed s/pattern/replacement/).

        Args:
            pattern: Regular expression pattern to match
            replacement: String to replace matches with
            value: Input string to transform

        Returns:
            String with replacements applied, or original value if regex is invalid

        Examples:
            regex_replace(' ohm$', '', '100 ohm') → '100'
            regex_replace('[^0-9]', '', 'R100K') → '100'
            regex_replace('o', 'x', 'foo') → 'fxx'
        """
        if value is None:
            return None
        try:
            return re.sub(pattern, replacement, value)
        except (re.error, TypeError):
            # Invalid regex pattern or null value - return original unchanged
            return value

    @functions.signature({'types': ['string', 'number', 'null']})
    def _func_int(self, value: Union[str, int, float, None]) -> Optional[int]:
        """
        Convert a value to an integer.

        Args:
            value: String or numeric value to convert

        Returns:
            Integer value, or None (JSON null) if conversion fails

        Examples:
            int('100') → 100
            int(42.7) → 42
            int('invalid') → null
            int('') → null

        Note:
            Returning null on failure allows safe filtering:
            Products[?int(Field) != null]
        """
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return int(value)
            return int(value)
        except (ValueError, TypeError):
            return None

    @functions.signature({'types': ['string', 'number', 'boolean', 'array', 'object', 'null']})
    def _func_str(self, value: Any) -> str:
        """
        Convert a value to a string.

        Args:
            value: Any value to convert to string

        Returns:
            String representation of the value

        Examples:
            str(100) → '100'
            str(42.7) → '42.7'
            str(true) → 'true'
            str(null) → 'null'

        Note:
            This is useful for concatenating numeric values or converting
            them for regex operations.
        """
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return str(value)

    @functions.signature(
        {'types': ['string', 'number', 'boolean', 'array', 'object', 'null']},
        {'types': ['string', 'number', 'boolean', 'array', 'object']}
    )
    def _func_nvl(self, value: Any, default: Any) -> Any:
        """
        Return default value if value is null (like Oracle's NVL function).

        Args:
            value: Value to check for null
            default: Default value to return if value is null

        Returns:
            Original value if not null, otherwise default value

        Examples:
            nvl(null, 'N/A') → 'N/A'
            nvl('existing', 'default') → 'existing'
            nvl(int(Field), 0) → 0 if Field is not a valid number

        Note:
            This is particularly useful with int() conversions:
            nvl(int(PriceString), 0) ensures a numeric value is always returned
        """
        if value is None:
            return default
        return value


# Create a shared options object with custom functions registered
_custom_options = jmespath.Options(custom_functions=CustomFunctions())


def search_with_custom_functions(expression: str, data: Any) -> Any:
    """
    Execute a JMESPath query with custom functions enabled.

    This is a drop-in replacement for jmespath.search() that includes
    custom regex_replace(), int(), str(), and nvl() functions.

    Args:
        expression: JMESPath query expression
        data: Data to query

    Returns:
        Query result

    Examples:
        >>> data = {"value": "100 ohm"}
        >>> search_with_custom_functions("int(regex_replace(' ohm$', '', value))", data)
        100

        >>> data = {"products": [{"resistance": "50 ohm"}, {"resistance": "150 ohm"}]}
        >>> query = "products[?int(regex_replace(' ohm$', '', resistance)) >= 100]"
        >>> search_with_custom_functions(query, data)
        [{"resistance": "150 ohm"}]

        >>> data = {"price": null}
        >>> search_with_custom_functions("nvl(price, 'N/A')", data)
        'N/A'
    """
    return jmespath.search(expression, data, options=_custom_options)
