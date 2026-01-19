import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("STARTING DATA TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Define input and output paths
    input_path = r'temp_uploads\sample_customer_data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] Created output directory: {output_dir}")
    
    # Load the Excel file
    print(f"\n[INFO] Loading data from: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] Data loaded successfully!")
        print(f"[INFO] Original shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"[INFO] Original columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display original data info
    print("\n[INFO] Original data preview:")
    print(df.head())
    
    # Check if 'Address' column exists
    print("\n[INFO] Checking for 'Address' column...")
    if 'Address' in df.columns:
        print("[INFO] 'Address' column found. Attempting to split into City and State...")
        
        # Split Address column into City and State
        # Assuming format like "City, State" or "City State"
        def split_address(address):
            if pd.isna(address):
                return pd.Series([None, None])
            
            address = str(address).strip()
            
            # Try splitting by comma first
            if ',' in address:
                parts = address.split(',', 1)
                city = parts[0].strip()
                state = parts[1].strip() if len(parts) > 1 else None
            # Try splitting by last space (assuming State is last word)
            elif ' ' in address:
                parts = address.rsplit(' ', 1)
                city = parts[0].strip()
                state = parts[1].strip() if len(parts) > 1 else None
            else:
                city = address
                state = None
            
            return pd.Series([city, state])
        
        # Apply the split
        df[['City', 'State']] = df['Address'].apply(split_address)
        print("[SUCCESS] Address column split into 'City' and 'State'")
        
        # Optionally keep or remove the original Address column
        # Keeping it for reference
        print("[INFO] Original 'Address' column retained for reference")
    else:
        print("[WARNING] 'Address' column not found in the dataset!")
        print(f"[INFO] Available columns: {list(df.columns)}")
        print("[INFO] Creating placeholder 'City' and 'State' columns with null values...")
        df['City'] = None
        df['State'] = None
    
    # Remove null values
    print("\n[INFO] Removing rows with null values...")
    original_row_count = len(df)
    
    # Count nulls before removal
    null_counts = df.isnull().sum()
    print("[INFO] Null counts per column before removal:")
    for col, count in null_counts.items():
        if count > 0:
            print(f"       - {col}: {count} nulls")
    
    # Remove rows with any null values
    df_cleaned = df.dropna()
    removed_rows = original_row_count - len(df_cleaned)
    
    print(f"[SUCCESS] Removed {removed_rows} rows containing null values")
    print(f"[INFO] Remaining rows: {len(df_cleaned)}")
    
    # If all rows were removed, keep original data with warning
    if len(df_cleaned) == 0:
        print("[WARNING] All rows contained null values! Keeping original data with nulls filled.")
        df_cleaned = df.fillna('')
        print(f"[INFO] Filled null values with empty strings. Row count: {len(df_cleaned)}")
    
    # Display transformed data info
    print("\n[INFO] Transformed data preview:")
    print(df_cleaned.head())
    print(f"\n[INFO] Final shape: {df_cleaned.shape[0]} rows, {df_cleaned.shape[1]} columns")
    print(f"[INFO] Final columns: {list(df_cleaned.columns)}")
    
    # Save to Excel
    print(f"\n[INFO] Saving to Excel: {output_xlsx}")
    try:
        df_cleaned.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"[SUCCESS] Excel file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    print(f"\n[INFO] Saving to JSON: {output_json}")
    try:
        df_cleaned.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"[SUCCESS] JSON file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"[SUMMARY]")
    print(f"  - Input file: {input_path}")
    print(f"  - Original rows: {original_row_count}")
    print(f"  - Final rows: {len(df_cleaned)}")
    print(f"  - Rows removed (nulls): {removed_rows}")
    print(f"  - Output Excel: {output_xlsx}")
    print(f"  - Output JSON: {output_json}")
    print("=" * 60)

if __name__ == "__main__":
    main()