"""
Prebuilt Transformation Library
Contains common functions for data cleaning, formatting, and calculation.
Designed to be Key-Error safe and easy to apply via pandas.apply().
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime, date
from typing import Union, Tuple, Optional, Any

# ==========================================
# CATEGORY 1: String Operations
# ==========================================

def split_name(full_name: Any) -> Tuple[Optional[str], Optional[str]]:
    """Split full name into first and last name. Returns (First, Last)."""
    if pd.isna(full_name) or not str(full_name).strip():
        return None, None
    
    parts = str(full_name).strip().split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]

def merge_name(first: Any, last: Any) -> str:
    """Merge first and last name into full name."""
    f = str(first).strip() if pd.notna(first) else ""
    l = str(last).strip() if pd.notna(last) else ""
    return f"{f} {l}".strip()

def extract_first_word(text: Any) -> str:
    if pd.isna(text): return ""
    return str(text).strip().split()[0] if str(text).strip() else ""

def to_uppercase(text: Any) -> str:
    return str(text).upper() if pd.notna(text) else ""

def to_lowercase(text: Any) -> str:
    return str(text).lower() if pd.notna(text) else ""

def to_titlecase(text: Any) -> str:
    return str(text).title() if pd.notna(text) else ""

def trim_whitespace(text: Any) -> str:
    return str(text).strip() if pd.notna(text) else ""

def remove_special_chars(text: Any) -> str:
    if pd.isna(text): return ""
    return re.sub(r'[^A-Za-z0-9\s]', '', str(text))

# ==========================================
# CATEGORY 2: Date Operations
# ==========================================

def parse_date(value: Any, input_format: Optional[str] = None) -> Union[date, pd.NaT]:
    """Parse date string to date object."""
    if pd.isna(value): return pd.NaT
    try:
        if input_format:
            return datetime.strptime(str(value), input_format).date()
        return pd.to_datetime(value).date()
    except:
        return pd.NaT

def calculate_age(dob: Any) -> Optional[int]:
    """Calculate age from date of birth."""
    birth_date = parse_date(dob)
    if pd.isna(birth_date): return None
    
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def days_between(d1: Any, d2: Any) -> Optional[int]:
    """Calculate days between two dates."""
    date1 = parse_date(d1)
    date2 = parse_date(d2)
    if pd.isna(date1) or pd.isna(date2): return None
    return abs((date2 - date1).days)

# ==========================================
# CATEGORY 3: Number Operations
# ==========================================

def to_float(value: Any) -> Optional[float]:
    """Safely convert to float, handling currency symbols."""
    if pd.isna(value): return None
    s = str(value).replace(',', '').replace('$', '').replace('€', '').replace('₹', '').strip()
    try:
        return float(s)
    except:
        return None

def round_number(value: Any, decimals: int = 2) -> Optional[float]:
    val = to_float(value)
    if val is None: return None
    return round(val, decimals)

# ==========================================
# CATEGORY 4: Contact Info
# ==========================================

def normalize_phone(phone: Any, country_code: str = "91") -> str:
    """Normalize phone number to digits only, optionally adding country code."""
    if pd.isna(phone): return ""
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 10 and country_code:
        return f"+{country_code}{digits}"
    return digits

def validate_email(email: Any) -> bool:
    """Simple email regex validation."""
    if pd.isna(email): return False
    # Basic regex
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", str(email)))

# ==========================================
# CATEGORY 7: Validation & Cleaning
# ==========================================

def fill_null_with(series: pd.Series, value: Any) -> pd.Series:
    return series.fillna(value)

def remove_duplicates(df: pd.DataFrame, subset: Optional[list] = None) -> pd.DataFrame:
    return df.drop_duplicates(subset=subset)

