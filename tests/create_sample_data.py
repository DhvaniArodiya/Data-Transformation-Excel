"""
Sample test data for AI Excel Transformation System.
Run this to create a sample messy Excel file for testing.
"""

import pandas as pd
from pathlib import Path


def create_sample_data():
    """Create a sample messy Excel file for testing."""
    
    # Sample messy customer data with common issues
    data = {
        'Cust_Name': [
            'John Doe',
            'Jane Smith',
            'Robert Johnson Jr.',
            'Mary',
            'Dr. William Brown',
            'Sarah Connor',
            'Michael Johnson',
            'Emily Davis Wilson',
            'James Bond',
            'Alice Wonderland',
        ],
        'Mobile_No': [
            '+91-9876543210',
            '9123456789',
            '91 8765432109',
            '(022) 12345678',
            '9999888877',
            '+919988776655',
            '98765-43210',
            '9876543210',
            '+91 99887 76655',
            '8765432100',
        ],
        'Email_ID': [
            'john.doe@gmail.com',
            'jane_smith@yahoo.com',
            'r.johnson@company.co.in',
            'mary123@hotmail.com',
            'wbrown@hospital.org',
            'sconnor@skynet.com',
            'mjohnson@email.com',
            'emily.wilson@domain.com',
            'bond.james@mi6.gov.uk',
            'alice@wonderland_inc.com',  # Invalid email
        ],
        'Pin_Code': [
            '400001',
            '110001',
            '560001',
            '600001',
            '700001',
            '500001',
            '380001',
            '411001',
            '400001',
            '110001',
        ],
        'Address_Line': [
            '123 Main Street, Bandra',
            '456 Park Avenue, Connaught Place',
            '789 Tech Park, Whitefield',
            '321 Beach Road, Marina',
            '654 Lake View, Salt Lake',
            '987 IT Hub, Hitech City',
            '147 Industrial Area, Naroda',
            '258 University Road, Shivajinagar',
            '369 Gateway Tower, Nariman Point',
            '741 Model Town',
        ],
        'GST_No': [
            '27AAAAA0000A1Z5',
            '07BBBBB1111B1Z4',
            '29CCCCC2222C1Z3',
            '33DDDDD3333D1Z2',
            '19EEEEE4444E1Z1',
            '36FFFFF5555F1Z0',
            '24GGGGG6666G1Z9',
            '27HHHHH7777H1Z8',
            '',  # Empty GSTIN
            '27JJJJJ9999J1Z6',
        ],
        'Order_Date': [
            '15/12/2024',
            '2024-12-10',
            '12-Dec-2024',
            '25/11/2024',
            '2024/11/20',
            '30-11-24',
            '05/12/2024',
            'December 1, 2024',
            '15/12/2024',
            '10/12/2024',
        ],
        'Amount': [
            '₹ 15,000.00',
            'Rs.25000',
            '35,000',
            'INR 45000.50',
            '₹55,000',
            '65000.00',
            'Rs 75,000.00',
            '85000',
            '₹95,000.50',
            'Rs.1,05,000',
        ],
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    output_path = Path(__file__).parent / "sample_messy_data.xlsx"
    df.to_excel(output_path, index=False, sheet_name="Customers")
    
    print(f"✅ Created sample data: {output_path}")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    
    return output_path


if __name__ == "__main__":
    create_sample_data()
