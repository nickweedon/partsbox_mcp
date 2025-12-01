"""
Tests for custom JMESPath functions.
"""

import pytest
from partsbox_mcp.utils.jmespath_extensions import search_with_custom_functions


class TestNvlFunction:
    """Tests for the nvl() function."""

    def test_nvl_returns_default_when_null(self):
        """nvl returns default when value is null."""
        data = {"value": None}
        result = search_with_custom_functions("nvl(value, 'default')", data)
        assert result == "default"

    def test_nvl_returns_value_when_not_null(self):
        """nvl returns value when it's not null."""
        data = {"value": "existing"}
        result = search_with_custom_functions("nvl(value, 'default')", data)
        assert result == "existing"

    def test_nvl_with_empty_string_default(self):
        """nvl works with empty string as default."""
        data = {"value": None}
        result = search_with_custom_functions("nvl(value, '')", data)
        assert result == ""

    def test_nvl_with_empty_array_default(self):
        """nvl works with empty array as default."""
        data = {"value": None}
        result = search_with_custom_functions("nvl(value, `[]`)", data)
        assert result == []

    def test_nvl_with_contains_null_safety(self):
        """nvl provides null safety when used with contains()."""
        data = {"part/name": None}
        # This should NOT raise an error - nvl should provide empty string default
        result = search_with_custom_functions(
            '[?contains(nvl("part/name", \'\'), \'test\')]',
            [data]
        )
        assert result == []

    def test_nvl_with_array_field_and_join(self):
        """nvl works with array fields piped to join()."""
        data = [{"part/tags": None}, {"part/tags": ["resistor", "smd"]}]
        # This is the pattern from the failing query
        result = search_with_custom_functions(
            '[?contains(nvl("part/tags", `[]`) | join(\',\', @), \'resistor\')]',
            data
        )
        assert len(result) == 1
        assert result[0]["part/tags"] == ["resistor", "smd"]

    def test_nvl_in_complex_or_query(self):
        """nvl works in complex OR queries with multiple conditions."""
        data = [
            {"part/name": "Inductor 10uH", "part/tags": None},
            {"part/name": None, "part/tags": ["inductor"]},
            {"part/name": "Resistor", "part/tags": ["resistor"]},
        ]
        # This is the pattern from the failing query
        query = """[?contains(nvl("part/name", ''), 'Inductor') || contains(nvl("part/tags", `[]`) | join(',', @), 'inductor')]"""
        result = search_with_custom_functions(query, data)
        assert len(result) == 2

    def test_nvl_rejects_null_default_value(self):
        """Test that nvl raises error when default value is null.

        This is intentional - null as default is never the intended behavior.
        The error helps catch incorrect JMESPath syntax like [] instead of `[]`.
        """
        data = {"value": None, "default_field": None}
        # nvl should reject null as default - this catches syntax errors
        with pytest.raises(Exception) as exc_info:
            search_with_custom_functions("nvl(value, default_field)", data)
        assert "invalid type for value: None" in str(exc_info.value)

    def test_nvl_rejects_unquoted_empty_array_default(self):
        """Test nvl rejects [] (unquoted) which evaluates to null in JMESPath.

        [] without backticks evaluates to null, not an empty array.
        nvl intentionally rejects null defaults to catch this common mistake.
        Use `[]` (with backticks) for a literal empty array.
        """
        data = {"part/tags": None}
        # [] without backticks evaluates to null - nvl should reject this
        with pytest.raises(Exception) as exc_info:
            search_with_custom_functions('nvl("part/tags", [])', data)
        assert "invalid type for value: None" in str(exc_info.value)

    def test_nvl_with_backtick_empty_array_default(self):
        """Test nvl with `[]` (backticks) which is a literal empty array."""
        data = {"part/tags": None}
        # `[]` with backticks is a literal empty array
        result = search_with_custom_functions('nvl("part/tags", `[]`)', data)
        assert result == []

    def test_exact_failing_query(self):
        """Test the exact query that failed in production."""
        # Simulating the actual data structure from PartsBox
        data = [
            {"part/id": "1", "part/name": "Inductor 10uH", "part/description": None, "part/mpn": None, "part/stock": 5, "part/tags": None},
            {"part/id": "2", "part/name": None, "part/description": "Some inductor", "part/mpn": "IND-001", "part/stock": 10, "part/tags": ["inductor"]},
            {"part/id": "3", "part/name": "Resistor 10K", "part/description": "SMD Resistor", "part/mpn": "RES-001", "part/stock": 100, "part/tags": ["resistor", "smd"]},
        ]

        # The exact query from the error (with backticks for literal empty array)
        query = '''[?contains(nvl("part/name", ''), 'inductor') || contains(nvl("part/name", ''), 'Inductor') || contains(nvl("part/tags", `[]`) | join(',', @), 'inductor')].{"id": "part/id", "name": "part/name", "description": "part/description", "mpn": "part/mpn", "stock": "part/stock", "tags": "part/tags"}'''

        result = search_with_custom_functions(query, data)
        # Should find 2 items - the one with "Inductor" in name and the one with "inductor" tag
        assert len(result) == 2

    def test_nvl_error_message_helps_identify_syntax_issue(self):
        """Test that nvl() error message helps identify the [] vs `[]` issue.

        When [] without backticks is used, it evaluates to null. The error
        message should make it clear that null is not allowed as default,
        helping users understand they need to use `[]` instead.
        """
        data = {"part/tags": None}

        # Using [] without backticks - should fail with helpful error
        with pytest.raises(Exception) as exc_info:
            search_with_custom_functions('nvl("part/tags", [])', data)

        error_msg = str(exc_info.value)
        # Error should mention nvl() and invalid type
        assert "nvl()" in error_msg
        assert "null" in error_msg.lower()


class TestIntFunction:
    """Tests for the int() function."""

    def test_int_converts_string(self):
        """int converts string to integer."""
        data = {"value": "100"}
        result = search_with_custom_functions("int(value)", data)
        assert result == 100

    def test_int_returns_null_for_invalid_string(self):
        """int returns null for non-numeric string."""
        data = {"value": "invalid"}
        result = search_with_custom_functions("int(value)", data)
        assert result is None

    def test_int_handles_null_input(self):
        """int handles null input gracefully."""
        data = {"value": None}
        result = search_with_custom_functions("int(value)", data)
        assert result is None


class TestStrFunction:
    """Tests for the str() function."""

    def test_str_converts_number(self):
        """str converts number to string."""
        data = {"value": 100}
        result = search_with_custom_functions("str(value)", data)
        assert result == "100"

    def test_str_handles_null(self):
        """str converts null to 'null' string."""
        data = {"value": None}
        result = search_with_custom_functions("str(value)", data)
        assert result == "null"


class TestRegexReplaceFunction:
    """Tests for the regex_replace() function."""

    def test_regex_replace_basic(self):
        """regex_replace performs basic substitution."""
        data = {"value": "100 ohm"}
        result = search_with_custom_functions("regex_replace(' ohm$', '', value)", data)
        assert result == "100"

    def test_regex_replace_handles_null(self):
        """regex_replace returns null when value is null."""
        data = {"value": None}
        result = search_with_custom_functions("regex_replace('x', 'y', value)", data)
        assert result is None
