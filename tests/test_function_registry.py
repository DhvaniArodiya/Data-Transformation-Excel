"""
Unit tests for Function Registry.
Tests all prebuilt transformation functions.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engine.function_registry import FunctionRegistry, get_registry


class TestFunctionRegistry:
    """Test the FunctionRegistry class."""
    
    @pytest.fixture
    def registry(self):
        """Create a fresh registry for each test."""
        return FunctionRegistry()
    
    # ========== String Functions ==========
    
    def test_split_full_name_two_parts(self, registry):
        """Test splitting name with first and last."""
        result = registry.execute("SPLIT_FULL_NAME", "John Doe", {})
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["middle_name"] == ""
    
    def test_split_full_name_three_parts(self, registry):
        """Test splitting name with middle name."""
        result = registry.execute("SPLIT_FULL_NAME", "John William Doe", {})
        assert result["first_name"] == "John"
        assert result["middle_name"] == "William"
        assert result["last_name"] == "Doe"
    
    def test_split_full_name_single(self, registry):
        """Test single name handling."""
        result = registry.execute("SPLIT_FULL_NAME", "Madonna", {})
        assert result["first_name"] == "Madonna"
        assert result["last_name"] == ""
    
    def test_split_full_name_comma_delimiter(self, registry):
        """Test comma-separated name."""
        result = registry.execute("SPLIT_FULL_NAME", "Doe, John", {"delimiter": ","})
        # With comma delimiter, it should still work
        assert "Doe" in str(result.values())
        assert "John" in str(result.values())
    
    def test_clean_whitespace(self, registry):
        """Test whitespace cleaning."""
        result = registry.execute("CLEAN_WHITESPACE", "  Hello   World  ", {})
        assert result == "Hello World"
    
    def test_uppercase(self, registry):
        """Test uppercase conversion."""
        result = registry.execute("UPPERCASE", "hello world", {})
        assert result == "HELLO WORLD"
    
    def test_lowercase(self, registry):
        """Test lowercase conversion."""
        result = registry.execute("LOWERCASE", "HELLO WORLD", {})
        assert result == "hello world"
    
    def test_titlecase(self, registry):
        """Test title case conversion."""
        result = registry.execute("TITLECASE", "hello world", {})
        assert result == "Hello World"
    
    def test_regex_extract(self, registry):
        """Test regex extraction."""
        result = registry.execute("REGEX_EXTRACT", "Email: john@example.com", {
            "pattern": r"[\w.-]+@[\w.-]+",
            "group_index": 0
        })
        assert result == "john@example.com"
    
    def test_concatenate(self, registry):
        """Test value concatenation."""
        result = registry.execute("CONCATENATE", None, {
            "separator": ", "
        }, values=["John", "Doe"])
        assert result == "John, Doe"
    
    # ========== Date Functions ==========
    
    def test_smart_date_parse_uk_format(self, registry):
        """Test UK date format parsing."""
        result = registry.execute("SMART_DATE_PARSE", "25/12/2024", {
            "ambiguity_preference": "UK"
        })
        assert result is not None
        assert result.day == 25
        assert result.month == 12
        assert result.year == 2024
    
    def test_smart_date_parse_iso_format(self, registry):
        """Test ISO date format parsing."""
        result = registry.execute("SMART_DATE_PARSE", "2024-12-25", {})
        assert result is not None
        assert result.year == 2024
    
    def test_format_date(self, registry):
        """Test date formatting."""
        result = registry.execute("FORMAT_DATE", "25/12/2024", {
            "target_format": "%Y-%m-%d"
        })
        assert result == "2024-12-25"
    
    # ========== Number Functions ==========
    
    def test_normalize_currency_rupees(self, registry):
        """Test currency normalization with Indian rupee."""
        result = registry.execute("NORMALIZE_CURRENCY", "₹ 15,000.50", {})
        assert result == 15000.50
    
    def test_normalize_currency_rs(self, registry):
        """Test currency normalization with Rs."""
        result = registry.execute("NORMALIZE_CURRENCY", "Rs.25,000", {})
        assert result == 25000.0
    
    def test_normalize_currency_plain(self, registry):
        """Test plain number normalization."""
        result = registry.execute("NORMALIZE_CURRENCY", "1,00,000", {})
        assert result == 100000.0
    
    # ========== Logic Functions ==========
    
    def test_map_values(self, registry):
        """Test value mapping."""
        result = registry.execute("MAP_VALUES", "yes", {
            "mapping_dict": {"yes": "Active", "no": "Inactive"},
            "default": "Unknown"
        })
        assert result == "Active"
    
    def test_map_values_default(self, registry):
        """Test value mapping with default."""
        result = registry.execute("MAP_VALUES", "maybe", {
            "mapping_dict": {"yes": "Active", "no": "Inactive"},
            "default": "Unknown"
        })
        assert result == "Unknown"
    
    # ========== Validation Functions ==========
    
    def test_validate_gstin_valid(self, registry):
        """Test valid GSTIN."""
        result = registry.execute("VALIDATE_GSTIN", "27AAAAA0000A1Z5", {})
        assert result["is_valid"] == True
        assert result["state_code"] == "27"
        assert result["pan"] == "AAAAA0000A"
    
    def test_validate_gstin_invalid(self, registry):
        """Test invalid GSTIN."""
        result = registry.execute("VALIDATE_GSTIN", "INVALID12345", {})
        assert result["is_valid"] == False
        assert result["error"] != ""
    
    def test_validate_email_valid(self, registry):
        """Test valid email."""
        result = registry.execute("VALIDATE_EMAIL", "test@example.com", {})
        assert result["is_valid"] == True
        assert result["normalized"] == "test@example.com"
    
    def test_validate_email_invalid(self, registry):
        """Test invalid email."""
        result = registry.execute("VALIDATE_EMAIL", "not-an-email", {})
        assert result["is_valid"] == False
    
    def test_normalize_phone_indian(self, registry):
        """Test Indian phone normalization."""
        result = registry.execute("NORMALIZE_PHONE", "9876543210", {
            "region": "IN",
            "format": "E.164"
        })
        assert result == "+919876543210"
    
    def test_normalize_phone_with_prefix(self, registry):
        """Test phone with country prefix."""
        result = registry.execute("NORMALIZE_PHONE", "+91-9876543210", {
            "region": "IN",
            "format": "E.164"
        })
        assert result == "+919876543210"
    
    # ========== Enrichment Functions ==========
    
    def test_lookup_pincode_known(self, registry):
        """Test pincode lookup for known pincode."""
        result = registry.execute("LOOKUP_PINCODE", "400001", {})
        assert result["city"] == "Mumbai"
        assert result["state"] == "Maharashtra"
    
    def test_lookup_pincode_unknown(self, registry):
        """Test pincode lookup for unknown pincode."""
        result = registry.execute("LOOKUP_PINCODE", "999999", {})
        assert result["country"] == "India"
    
    # ========== Null Handling ==========
    
    def test_null_handling(self, registry):
        """Test that functions handle None values gracefully."""
        assert registry.execute("CLEAN_WHITESPACE", None, {}) == ""
        assert registry.execute("UPPERCASE", None, {}) == ""
        assert registry.execute("NORMALIZE_CURRENCY", None, {}) is None
    
    def test_empty_string_handling(self, registry):
        """Test that functions handle empty strings."""
        assert registry.execute("CLEAN_WHITESPACE", "", {}) == ""
        assert registry.execute("TRIM", "   ", {}) == ""


class TestFunctionList:
    """Test that all expected functions are registered."""
    
    def test_all_functions_registered(self):
        """Verify all expected functions exist."""
        registry = get_registry()
        functions = registry.list_functions()
        
        expected = [
            "SPLIT_FULL_NAME", "REGEX_EXTRACT", "CLEAN_WHITESPACE",
            "SMART_DATE_PARSE", "FORMAT_DATE", "NORMALIZE_CURRENCY",
            "MAP_VALUES", "CONDITIONAL_FILL", "LOOKUP_PINCODE",
            "VALIDATE_GSTIN", "VALIDATE_EMAIL", "NORMALIZE_PHONE",
            "UPPERCASE", "LOWERCASE", "TITLECASE", "TRIM", "CONCATENATE"
        ]
        
        for func in expected:
            assert func in functions, f"Missing function: {func}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
