import pandas as pd
import sys
import os
from datetime import datetime

def main():
    # Configuration
    input_file = 'temp_uploads/invoice_data (3).csv'
    output_dir = 'output'
    output_file = os.path.join(output_dir, 'Custom_Customer_Enhanced_fallback.xlsx')
    
    print("=" * 60)
    print("DATA TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] Created output directory: {output_dir}")
    
    # Load the source file
    print(f"\n[INFO] Loading source file: {input_file}")
    try:
        # Check file extension and load accordingly
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        else:
            df = pd.read_excel(input_file)
        print(f"[INFO] Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"[INFO] Source columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display source data info
    print(f"\n[INFO] Source data preview:")
    print(df.head())
    
    # Initialize target dataframe
    print("\n[INFO] Starting transformation...")
    target_df = pd.DataFrame()
    
    # The source schema has: itemName, quantity, price
    # The target schema requires customer data which doesn't exist in source
    # We need to create placeholder/default values since source doesn't have customer info
    
    print("[WARNING] Source data contains invoice items (itemName, quantity, price)")
    print("[WARNING] Target schema requires customer data - creating placeholder values")
    
    # Create target columns with appropriate defaults/placeholders
    num_rows = len(df)
    
    # First Name - placeholder
    if 'First Name' in df.columns:
        target_df['First Name'] = df['First Name'].astype(str)
    else:
        target_df['First Name'] = 'Unknown'
        print("[INFO] 'First Name' not in source - using placeholder 'Unknown'")
    
    # Last Name - placeholder
    if 'Last Name' in df.columns:
        target_df['Last Name'] = df['Last Name'].astype(str)
    else:
        target_df['Last Name'] = 'Customer'
        print("[INFO] 'Last Name' not in source - using placeholder 'Customer'")
    
    # Gender - placeholder
    if 'Gender' in df.columns:
        target_df['Gender'] = df['Gender'].astype(str)
    else:
        target_df['Gender'] = 'Unknown'
        print("[INFO] 'Gender' not in source - using placeholder 'Unknown'")
    
    # Country - placeholder
    if 'Country' in df.columns:
        target_df['Country'] = df['Country'].astype(str)
    else:
        target_df['Country'] = 'Unknown'
        print("[INFO] 'Country' not in source - using placeholder 'Unknown'")
    
    # Age - placeholder
    if 'Age' in df.columns:
        target_df['Age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(0).astype(int)
    else:
        target_df['Age'] = 30  # Default age
        print("[INFO] 'Age' not in source - using default value 30")
    
    # Date - placeholder with current date
    if 'Date' in df.columns:
        target_df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    else:
        target_df['Date'] = pd.to_datetime('2020-01-01')
        print("[INFO] 'Date' not in source - using default date '2020-01-01'")
    
    # Id - generate unique IDs
    if 'Id' in df.columns:
        target_df['Id'] = pd.to_numeric(df['Id'], errors='coerce').fillna(0).astype(int)
    else:
        target_df['Id'] = range(1, num_rows + 1)
        print("[INFO] 'Id' not in source - generating sequential IDs")
    
    # full_name - CONCATENATE: 'First Name' + ' ' + 'Last Name'
    print("[INFO] Computing 'full_name' = First Name + ' ' + Last Name")
    target_df['full_name'] = target_df['First Name'].astype(str) + ' ' + target_df['Last Name'].astype(str)
    
    # age_at_current - COMPUTE: Age + years_between(Date, '2025-12-31')
    print("[INFO] Computing 'age_at_current' = Age + years between Date and 2025-12-31")
    reference_date = pd.to_datetime('2025-12-31')
    
    def calculate_years_between(date_val):
        try:
            if pd.isna(date_val):
                return 0
            return (reference_date - pd.to_datetime(date_val)).days // 365
        except:
            return 0
    
    years_diff = target_df['Date'].apply(calculate_years_between)
    target_df['age_at_current'] = target_df['Age'] + years_diff
    target_df['age_at_current'] = target_df['age_at_current'].astype(int)
    
    # Format Date column for output
    target_df['Date'] = pd.to_datetime(target_df['Date']).dt.date
    
    # Select only target columns in the specified order
    target_columns = ['First Name', 'Last Name', 'Gender', 'Country', 'Age', 'Date', 'Id', 'full_name', 'age_at_current']
    target_df = target_df[target_columns]
    
    print(f"\n[INFO] Transformation complete!")
    print(f"[INFO] Target columns: {list(target_df.columns)}")
    print(f"\n[INFO] Target data preview:")
    print(target_df.head())
    
    # Save to output file
    print(f"\n[INFO] Saving to: {output_file}")
    try:
        target_df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"[SUCCESS] File saved successfully!")
        print(f"[INFO] Output contains {len(target_df)} rows and {len(target_df.columns)} columns")
    except Exception as e:
        print(f"[ERROR] Failed to save file: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    main()