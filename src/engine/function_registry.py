"""
Function Registry - The "Toolbox" of prebuilt transformation functions.
These are deterministic, tested functions that the Execution Engine uses.
The AI agents merely CONFIGURE these functions; they don't generate code.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import phonenumbers


class FunctionRegistry:
    """
    Registry of all available transformation functions.
    Each function is a pure function: (value, params) -> transformed_value
    """
    
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._register_all_functions()
    
    def _register_all_functions(self):
        """Register all built-in transformation functions."""
        self.register("SPLIT_FULL_NAME", self.split_full_name)
        self.register("REGEX_EXTRACT", self.regex_extract)
        self.register("CLEAN_WHITESPACE", self.clean_whitespace)
        self.register("SMART_DATE_PARSE", self.smart_date_parse)
        self.register("FORMAT_DATE", self.format_date)
        self.register("NORMALIZE_CURRENCY", self.normalize_currency)
        self.register("MAP_VALUES", self.map_values)
        self.register("CONDITIONAL_FILL", self.conditional_fill)
        self.register("LOOKUP_PINCODE", self.lookup_pincode)
        self.register("VALIDATE_GSTIN", self.validate_gstin)
        self.register("VALIDATE_EMAIL", self.validate_email)
        self.register("NORMALIZE_PHONE", self.normalize_phone)
        self.register("UPPERCASE", self.uppercase)
        self.register("LOWERCASE", self.lowercase)
        self.register("TITLECASE", self.titlecase)
        self.register("TRIM", self.trim)
        self.register("CONCATENATE", self.concatenate)
        self.register("COMPUTE_DATE_DIFF", self.compute_date_diff)
    
    def register(self, name: str, func: Callable):
        """Register a function with the given name."""
        self._functions[name.upper()] = func
    
    def get(self, name: str) -> Optional[Callable]:
        """Get a function by name."""
        return self._functions.get(name.upper())
    
    def execute(self, name: str, value: Any, params: Dict[str, Any] = None, **kwargs) -> Any:
        """Execute a registered function with the given value and parameters."""
        func = self.get(name)
        if func is None:
            raise ValueError(f"Unknown function: {name}")
        return func(value, params or {}, **kwargs)
    
    def list_functions(self) -> List[str]:
        """List all registered function names."""
        return list(self._functions.keys())
    
    # ===== STRING FUNCTIONS =====
    
    @staticmethod
    def split_full_name(value: Any, params: Dict[str, Any], **kwargs) -> Dict[str, str]:
        """
        Split a full name into first, middle, and last name components.
        
        Params:
            delimiter: str - Character to split on (default: auto-detect space/comma)
            culture: str - 'western' (first last) or 'eastern' (last first)
            handle_single_name: str - 'first_name_only', 'last_name_only'
        """
        if pd.isna(value) or value is None:
            return {"first_name": "", "middle_name": "", "last_name": ""}
        
        value = str(value).strip()
        if not value:
            return {"first_name": "", "middle_name": "", "last_name": ""}
        
        delimiter = params.get("delimiter", "auto")
        culture = params.get("culture", "western")
        handle_single = params.get("handle_single_name", "first_name_only")
        
        # Auto-detect delimiter
        if delimiter == "auto":
            if "," in value:
                delimiter = ","
            else:
                delimiter = " "
        
        parts = [p.strip() for p in value.split(delimiter) if p.strip()]
        
        if len(parts) == 0:
            return {"first_name": "", "middle_name": "", "last_name": ""}
        elif len(parts) == 1:
            if handle_single == "last_name_only":
                return {"first_name": "", "middle_name": "", "last_name": parts[0]}
            else:
                return {"first_name": parts[0], "middle_name": "", "last_name": ""}
        elif len(parts) == 2:
            if culture == "eastern":
                return {"first_name": parts[1], "middle_name": "", "last_name": parts[0]}
            else:
                return {"first_name": parts[0], "middle_name": "", "last_name": parts[1]}
        else:
            if culture == "eastern":
                return {"first_name": parts[-1], "middle_name": " ".join(parts[1:-1]), "last_name": parts[0]}
            else:
                return {"first_name": parts[0], "middle_name": " ".join(parts[1:-1]), "last_name": parts[-1]}
    
    @staticmethod
    def regex_extract(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """
        Extract a substring using regex pattern.
        
        Params:
            pattern: str - Regex pattern with groups
            group_index: int - Which group to extract (0 for full match)
        """
        if pd.isna(value) or value is None:
            return ""
        
        pattern = params.get("pattern", "")
        group_index = params.get("group_index", 0)
        
        if not pattern:
            return str(value)
        
        try:
            match = re.search(pattern, str(value))
            if match:
                if group_index == 0:
                    return match.group(0)
                elif group_index <= len(match.groups()):
                    return match.group(group_index)
            return ""
        except re.error:
            return ""
    
    @staticmethod
    def clean_whitespace(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """Remove extra whitespace, trim, and normalize spaces."""
        if pd.isna(value) or value is None:
            return ""
        result = str(value).strip()
        result = re.sub(r'\s+', ' ', result)
        return result
    
    @staticmethod
    def uppercase(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """Convert to uppercase."""
        if pd.isna(value) or value is None:
            return ""
        return str(value).upper()
    
    @staticmethod
    def lowercase(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """Convert to lowercase."""
        if pd.isna(value) or value is None:
            return ""
        return str(value).lower()
    
    @staticmethod
    def titlecase(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """Convert to title case."""
        if pd.isna(value) or value is None:
            return ""
        return str(value).title()
    
    @staticmethod
    def trim(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """Trim leading and trailing whitespace."""
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()
    
    @staticmethod
    def concatenate(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """
        Concatenate multiple values with a separator.
        Value should be a list or the kwargs should contain 'values'.
        
        Params:
            separator: str - Separator between values (default: " ")
        """
        separator = params.get("separator", " ")
        values = kwargs.get("values", [value] if not isinstance(value, list) else value)
        
        str_values = []
        for v in values:
            if not pd.isna(v) and v is not None:
                str_values.append(str(v).strip())
        
        return separator.join(str_values)
    
    
    # ===== DATE FUNCTIONS =====
    
    @staticmethod
    def compute_date_diff(value: Any, params: Dict[str, Any], **kwargs) -> Optional[int]:
        """
        Compute difference between two dates in days.
        Returns: (date1 - date2).days
        
        Params:
            date2_col: str - Column name for the second date (subtrahend)
        """
        if pd.isna(value) or value is None:
            return None
            
        params = params or {}
        row = kwargs.get("row", {})
        date2_col = params.get("date2_col")
        
        date1 = FunctionRegistry.smart_date_parse(value, params)
        if not date1:
            return None
            
        if not date2_col or date2_col not in row:
            # Check if provided via 'values' list (for multi-column input)
            values = kwargs.get("values", [])
            if len(values) >= 2:
                # Assuming value is values[0], date2 is values[1]
                date2 = FunctionRegistry.smart_date_parse(values[1], params)
            else:
                return None
        else:
            date2 = FunctionRegistry.smart_date_parse(row[date2_col], params)
            
        if not date2:
            return None
            
        return (date1 - date2).days

    @staticmethod
    def smart_date_parse(value: Any, params: Dict[str, Any], **kwargs) -> Optional[datetime]:
        """
        Parse dates handling multiple formats intelligently.
        
        Params:
            ambiguity_preference: str - 'US' (MM/DD), 'UK' (DD/MM), 'ISO' (YYYY-MM-DD)
        """
        if pd.isna(value) or value is None:
            return None
        
        value_str = str(value).strip()
        if not value_str:
            return None
        
        preference = params.get("ambiguity_preference", "UK")  # Default to DD/MM for India
        
        # Common date formats to try
        formats = []
        
        if preference == "US":
            formats = [
                "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y",
                "%Y-%m-%d", "%Y/%m/%d",
                "%d %b %Y", "%d %B %Y",
                "%b %d, %Y", "%B %d, %Y",
            ]
        elif preference == "ISO":
            formats = [
                "%Y-%m-%d", "%Y/%m/%d",
                "%d/%m/%Y", "%d-%m-%Y",
                "%d %b %Y", "%d %B %Y",
            ]
        else:  # UK/India (DD/MM)
            formats = [
                "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y",
                "%Y-%m-%d", "%Y/%m/%d",
                "%d %b %Y", "%d %B %Y",
                "%d-%b-%Y", "%d-%B-%Y",
            ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value_str, fmt)
            except ValueError:
                continue
        
        # Try pandas as last resort
        try:
            parsed = pd.to_datetime(value_str, dayfirst=(preference != "US"))
            return parsed.to_pydatetime()
        except:
            return None
    
    @staticmethod
    def format_date(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """
        Format a date to a specific format.
        
        Params:
            target_format: str - Output format (default: ISO8601 '%Y-%m-%d')
        """
        target_format = params.get("target_format", "%Y-%m-%d")
        
        if pd.isna(value) or value is None:
            return ""
        
        # If it's already a datetime
        if isinstance(value, datetime):
            return value.strftime(target_format)
        
        # Try to parse first
        parsed = FunctionRegistry.smart_date_parse(value, params, **kwargs)
        if parsed:
            return parsed.strftime(target_format)
        
        return str(value)
    
    # ===== NUMBER FUNCTIONS =====
    
    @staticmethod
    def normalize_currency(value: Any, params: Dict[str, Any], **kwargs) -> Optional[float]:
        """
        Normalize currency values by removing symbols and fixing decimals.
        
        Params:
            currency_symbol: str - Symbol to remove (default: auto-detect)
        """
        if pd.isna(value) or value is None:
            return None
        
        value_str = str(value).strip()
        if not value_str:
            return None
        
        # Remove common currency symbols
        symbols = ["$", "€", "£", "¥", "₹", "Rs", "Rs.", "INR", "USD", "EUR"]
        for symbol in symbols:
            value_str = value_str.replace(symbol, "")
        
        # Remove commas and spaces
        value_str = value_str.replace(",", "").replace(" ", "").strip()
        
        # Handle negative in parentheses
        if value_str.startswith("(") and value_str.endswith(")"):
            value_str = "-" + value_str[1:-1]
        
        try:
            return float(value_str)
        except ValueError:
            return None
    
    # ===== LOGIC FUNCTIONS =====
    
    @staticmethod
    def map_values(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """
        Map values using a dictionary.
        
        Params:
            mapping_dict: Dict[str, str] - Mapping of source to target values
            default: str - Default value if not found
        """
        if pd.isna(value) or value is None:
            return params.get("default", "")
        
        mapping = params.get("mapping_dict", {})
        default = params.get("default", str(value))
        
        value_str = str(value).strip().lower()
        
        # Try exact match (case-insensitive)
        for k, v in mapping.items():
            if k.lower() == value_str:
                return v
        
        return default
    
    @staticmethod
    def conditional_fill(value: Any, params: Dict[str, Any], **kwargs) -> Any:
        """
        Fill empty values with a fallback.
        
        Params:
            fallback_col: str - Name of fallback column (passed via kwargs['row'])
        """
        if pd.isna(value) or value is None or str(value).strip() == "":
            fallback_col = params.get("fallback_col")
            row = kwargs.get("row")
            if row is not None and fallback_col and fallback_col in row:
                return row[fallback_col]
            return params.get("default", "")
        return value
    
    # ===== ENRICHMENT FUNCTIONS =====
    
    @staticmethod
    def lookup_pincode(value: Any, params: Dict[str, Any], **kwargs) -> Dict[str, str]:
        """
        Look up city/state from pincode.
        Currently returns a mock response. Integrate real API later.
        
        Params:
            provider: str - API provider to use
            cache_ttl: int - Cache TTL in seconds
        """
        if pd.isna(value) or value is None:
            return {"city": "", "state": "", "country": ""}
        
        pincode = str(value).strip()
        
        # Mock data for common Indian pincodes
        mock_data = {
            "400001": {"city": "Mumbai", "state": "Maharashtra", "country": "India"},
            "110001": {"city": "New Delhi", "state": "Delhi", "country": "India"},
            "560001": {"city": "Bangalore", "state": "Karnataka", "country": "India"},
            "600001": {"city": "Chennai", "state": "Tamil Nadu", "country": "India"},
            "700001": {"city": "Kolkata", "state": "West Bengal", "country": "India"},
            "500001": {"city": "Hyderabad", "state": "Telangana", "country": "India"},
            "380001": {"city": "Ahmedabad", "state": "Gujarat", "country": "India"},
            "411001": {"city": "Pune", "state": "Maharashtra", "country": "India"},
        }
        
        return mock_data.get(pincode, {"city": "", "state": "", "country": "India"})
    
    # ===== VALIDATION FUNCTIONS =====
    
    @staticmethod
    def validate_gstin(value: Any, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Validate Indian GSTIN and return validity + extracted info.
        
        GSTIN Format: 22AAAAA0000A1Z5
        - Position 1-2: State Code
        - Position 3-12: PAN
        - Position 13: Entity Number
        - Position 14: 'Z' (default)
        - Position 15: Checksum
        """
        result = {"is_valid": False, "state_code": "", "pan": "", "error": ""}
        
        if pd.isna(value) or value is None:
            result["error"] = "Empty value"
            return result
        
        gstin = str(value).strip().upper()
        
        if len(gstin) != 15:
            result["error"] = f"Invalid length: {len(gstin)} (expected 15)"
            return result
        
        # Basic pattern check
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$'
        if not re.match(pattern, gstin):
            result["error"] = "Invalid format"
            return result
        
        result["is_valid"] = True
        result["state_code"] = gstin[:2]
        result["pan"] = gstin[2:12]
        return result
    
    @staticmethod
    def validate_email(value: Any, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Validate email format."""
        result = {"is_valid": False, "normalized": "", "error": ""}
        
        if pd.isna(value) or value is None:
            result["error"] = "Empty value"
            return result
        
        email = str(value).strip().lower()
        
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if re.match(pattern, email):
            result["is_valid"] = True
            result["normalized"] = email
        else:
            result["error"] = "Invalid email format"
        
        return result
    
    @staticmethod
    def normalize_phone(value: Any, params: Dict[str, Any], **kwargs) -> str:
        """
        Normalize phone number to standard format.
        
        Params:
            region: str - ISO country code (default: 'IN')
            format: str - 'E.164', 'NATIONAL', 'INTERNATIONAL'
        """
        if pd.isna(value) or value is None:
            return ""
        
        phone_str = str(value).strip()
        if not phone_str:
            return ""
        
        region = params.get("region", "IN")
        output_format = params.get("format", "E.164")
        
        try:
            parsed = phonenumbers.parse(phone_str, region)
            
            if not phonenumbers.is_valid_number(parsed):
                return phone_str  # Return original if invalid
            
            if output_format == "NATIONAL":
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
            elif output_format == "INTERNATIONAL":
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            else:  # E.164
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.phonenumberutil.NumberParseException:
            return phone_str  # Return original if parsing fails


# Global registry instance
_registry: Optional[FunctionRegistry] = None


def get_registry() -> FunctionRegistry:
    """Get or create the global function registry."""
    global _registry
    if _registry is None:
        _registry = FunctionRegistry()
    return _registry
