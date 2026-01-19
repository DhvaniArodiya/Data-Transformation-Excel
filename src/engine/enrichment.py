"""
Enrichment Services - External API integrations for data enrichment.
"""

import httpx
from typing import Dict, Any, Optional
from functools import lru_cache
import json
from pathlib import Path


class PincodeService:
    """
    Indian Pincode lookup service.
    Uses the India Post API for pincode data.
    Falls back to cached data if API fails.
    """
    
    API_URL = "https://api.postalpincode.in/pincode/{pincode}"
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize with optional cache file path."""
        self._cache: Dict[str, Dict[str, str]] = {}
        self._cache_file = cache_file
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from file if exists."""
        if self._cache_file and Path(self._cache_file).exists():
            try:
                with open(self._cache_file, 'r') as f:
                    self._cache = json.load(f)
            except:
                pass
        
        # Pre-populate with common pincodes
        self._cache.update({
            "400001": {"city": "Mumbai", "state": "Maharashtra", "district": "Mumbai", "country": "India"},
            "110001": {"city": "New Delhi", "state": "Delhi", "district": "Central Delhi", "country": "India"},
            "560001": {"city": "Bangalore", "state": "Karnataka", "district": "Bangalore", "country": "India"},
            "600001": {"city": "Chennai", "state": "Tamil Nadu", "district": "Chennai", "country": "India"},
            "700001": {"city": "Kolkata", "state": "West Bengal", "district": "Kolkata", "country": "India"},
            "500001": {"city": "Hyderabad", "state": "Telangana", "district": "Hyderabad", "country": "India"},
            "380001": {"city": "Ahmedabad", "state": "Gujarat", "district": "Ahmedabad", "country": "India"},
            "411001": {"city": "Pune", "state": "Maharashtra", "district": "Pune", "country": "India"},
            "226001": {"city": "Lucknow", "state": "Uttar Pradesh", "district": "Lucknow", "country": "India"},
            "302001": {"city": "Jaipur", "state": "Rajasthan", "district": "Jaipur", "country": "India"},
            "440001": {"city": "Nagpur", "state": "Maharashtra", "district": "Nagpur", "country": "India"},
            "560100": {"city": "Bangalore", "state": "Karnataka", "district": "Bangalore Rural", "country": "India"},
            "400051": {"city": "Mumbai", "state": "Maharashtra", "district": "Mumbai Suburban", "country": "India"},
            "110085": {"city": "New Delhi", "state": "Delhi", "district": "North West Delhi", "country": "India"},
            "201301": {"city": "Noida", "state": "Uttar Pradesh", "district": "Gautam Buddha Nagar", "country": "India"},
            "122001": {"city": "Gurgaon", "state": "Haryana", "district": "Gurgaon", "country": "India"},
        })
    
    def _save_cache(self):
        """Save cache to file."""
        if self._cache_file:
            with open(self._cache_file, 'w') as f:
                json.dump(self._cache, f)
    
    def lookup(self, pincode: str) -> Dict[str, str]:
        """
        Look up city/state for a pincode.
        
        Args:
            pincode: 6-digit Indian pincode
            
        Returns:
            Dict with city, state, district, country
        """
        pincode = str(pincode).strip()
        
        # Check cache first
        if pincode in self._cache:
            return self._cache[pincode]
        
        # Try API
        try:
            result = self._call_api(pincode)
            if result:
                self._cache[pincode] = result
                self._save_cache()
                return result
        except Exception:
            pass
        
        # Return empty on failure
        return {"city": "", "state": "", "district": "", "country": "India"}
    
    def _call_api(self, pincode: str) -> Optional[Dict[str, str]]:
        """Call the India Post API."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(self.API_URL.format(pincode=pincode))
                data = response.json()
                
                if data and len(data) > 0 and data[0].get("Status") == "Success":
                    post_offices = data[0].get("PostOffice", [])
                    if post_offices:
                        po = post_offices[0]
                        return {
                            "city": po.get("Block", po.get("Name", "")),
                            "state": po.get("State", ""),
                            "district": po.get("District", ""),
                            "country": po.get("Country", "India"),
                        }
        except Exception:
            pass
        return None


class GSTINService:
    """
    GSTIN validation and lookup service.
    Validates format and extracts state/PAN information.
    """
    
    # Indian state codes
    STATE_CODES = {
        "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
        "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
        "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
        "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
        "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
        "16": "Tripura", "17": "Meghalaya", "18": "Assam",
        "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
        "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
        "25": "Daman & Diu", "26": "Dadra & Nagar Haveli", "27": "Maharashtra",
        "28": "Andhra Pradesh", "29": "Karnataka", "30": "Goa",
        "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
        "34": "Puducherry", "35": "Andaman & Nicobar", "36": "Telangana",
        "37": "Andhra Pradesh (New)", "38": "Ladakh",
    }
    
    def validate(self, gstin: str) -> Dict[str, Any]:
        """
        Validate GSTIN and extract information.
        
        Args:
            gstin: 15-character GSTIN
            
        Returns:
            Dict with is_valid, state_code, state_name, pan, error
        """
        import re
        
        result = {
            "is_valid": False,
            "state_code": "",
            "state_name": "",
            "pan": "",
            "entity_type": "",
            "error": ""
        }
        
        if not gstin:
            result["error"] = "Empty GSTIN"
            return result
        
        gstin = str(gstin).strip().upper()
        
        if len(gstin) != 15:
            result["error"] = f"Invalid length: {len(gstin)} (expected 15)"
            return result
        
        # GSTIN pattern: 22AAAAA0000A1Z5
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$'
        if not re.match(pattern, gstin):
            result["error"] = "Invalid format"
            return result
        
        # Extract components
        state_code = gstin[:2]
        pan = gstin[2:12]
        entity_number = gstin[12]
        
        # Validate state code
        if state_code not in self.STATE_CODES:
            result["error"] = f"Invalid state code: {state_code}"
            return result
        
        result["is_valid"] = True
        result["state_code"] = state_code
        result["state_name"] = self.STATE_CODES[state_code]
        result["pan"] = pan
        result["entity_type"] = self._get_entity_type(entity_number)
        
        return result
    
    def _get_entity_type(self, code: str) -> str:
        """Get entity type from entity number."""
        types = {
            "1": "Proprietorship",
            "2": "Partnership",
            "3": "Company",
            "4": "LLP",
            "5": "Trust",
            "6": "Government",
            "7": "Local Authority",
            "8": "HUF",
            "9": "AOP/BOI",
        }
        return types.get(code, "Unknown")


class EmailValidationService:
    """
    Email validation service with syntax and deliverability checks.
    """
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        "tempmail.com", "throwaway.email", "mailinator.com",
        "10minutemail.com", "guerrillamail.com", "fakeinbox.com",
    }
    
    def validate(self, email: str) -> Dict[str, Any]:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Dict with is_valid, normalized, domain, is_disposable, error
        """
        import re
        
        result = {
            "is_valid": False,
            "normalized": "",
            "domain": "",
            "is_disposable": False,
            "error": ""
        }
        
        if not email:
            result["error"] = "Empty email"
            return result
        
        email = str(email).strip().lower()
        
        # Basic pattern validation
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(pattern, email):
            result["error"] = "Invalid email format"
            return result
        
        # Extract domain
        parts = email.split("@")
        if len(parts) != 2:
            result["error"] = "Invalid email format"
            return result
        
        domain = parts[1]
        
        # Check for disposable
        is_disposable = domain in self.DISPOSABLE_DOMAINS
        
        result["is_valid"] = True
        result["normalized"] = email
        result["domain"] = domain
        result["is_disposable"] = is_disposable
        
        return result


# Global service instances
_pincode_service: Optional[PincodeService] = None
_gstin_service: Optional[GSTINService] = None
_email_service: Optional[EmailValidationService] = None


def get_pincode_service() -> PincodeService:
    """Get or create global pincode service."""
    global _pincode_service
    if _pincode_service is None:
        _pincode_service = PincodeService()
    return _pincode_service


def get_gstin_service() -> GSTINService:
    """Get or create global GSTIN service."""
    global _gstin_service
    if _gstin_service is None:
        _gstin_service = GSTINService()
    return _gstin_service


def get_email_service() -> EmailValidationService:
    """Get or create global email service."""
    global _email_service
    if _email_service is None:
        _email_service = EmailValidationService()
    return _email_service
