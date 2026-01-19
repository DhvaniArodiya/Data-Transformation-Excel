import sys
from pathlib import Path
import unittest
import pandas as pd
from datetime import date

# Add src to path
sys.path.insert(0, str(Path.cwd()))

from src.utils.transformations import (
    split_name, to_uppercase, parse_date, calculate_age, 
    to_float, normalize_phone
)

class TestTransformationLibrary(unittest.TestCase):
    def test_string_ops(self):
        self.assertEqual(split_name("John Doe"), ("John", "Doe"))
        self.assertEqual(to_uppercase("hello"), "HELLO")
        
    def test_date_ops(self):
        d = parse_date("2020-01-01")
        self.assertEqual(d, date(2020, 1, 1))
        # Age calculation (Mocking logic needed? No, just basic check)
        age = calculate_age("2000-01-01")
        # Age should be roughly current year - 2000. 
        current_year = date.today().year
        self.assertTrue(current_year - 2001 <= age <= current_year - 2000)

    def test_number_ops(self):
        self.assertEqual(to_float("$1,234.56"), 1234.56)
        self.assertEqual(to_float("₹ 500"), 500.0)
        
    def test_contact_ops(self):
        self.assertEqual(normalize_phone("(123) 456-7890", country_code="1"), "+11234567890")
        self.assertEqual(normalize_phone("9876543210", country_code="91"), "+919876543210")

if __name__ == '__main__':
    unittest.main()
