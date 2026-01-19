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
    
    # Load the source file
    print(f"\n[INFO] Loading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] File loaded successfully!")
        print(f"[INFO] Original shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"[INFO] Original columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display first few rows of original data
    print("\n[INFO] Preview of original data:")
    print(df.head(3).to_string())
    
    # TRANSFORMATION: Merge First Name and Last Name into Full Name
    print("\n" + "=" * 60)
    print("APPLYING TRANSFORMATION")
    print("=" * 60)
    print("[INFO] Merging 'First Name' and 'Last Name' into 'Full Name'...")
    
    # Check if required columns exist
    if 'First Name' not in df.columns:
        print("[ERROR] Column 'First Name' not found in the data!")
        sys.exit(1)
    if 'Last Name' not in df.columns:
        print("[ERROR] Column 'Last Name' not found in the data!")
        sys.exit(1)
    
    # Handle potential null values gracefully
    df['First Name'] = df['First Name'].fillna('')
    df['Last Name'] = df['Last Name'].fillna('')
    
    # Create Full Name column by concatenating First Name and Last Name
    df['Full Name'] = df['First Name'].astype(str).str.strip() + ' ' + df['Last Name'].astype(str).str.strip()
    df['Full Name'] = df['Full Name'].str.strip()  # Remove any leading/trailing spaces
    
    print("[SUCCESS] 'Full Name' column created successfully!")
    
    # Reorder columns to put Full Name first, then remove First Name and Last Name
    # Keep all other original columns
    other_columns = [col for col in df.columns if col not in ['First Name', 'Last Name', 'Full Name']]
    new_column_order = ['Full Name'] + other_columns
    df_transformed = df[new_column_order]
    
    print(f"[INFO] Removed 'First Name' and 'Last Name' columns")
    print(f"[INFO] New columns: {list(df_transformed.columns)}")
    print(f"[INFO] Transformed shape: {df_transformed.shape[0]} rows x {df_transformed.shape[1]} columns")
    
    # Display preview of transformed data
    print("\n[INFO] Preview of transformed data:")
    print(df_transformed.head(3).to_string())
    
    # Save results
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    # Save to Excel
    try:
        df_transformed.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"[SUCCESS] Saved Excel file: {output_xlsx}")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    try:
        df_transformed.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"[SUCCESS] Saved JSON file: {output_json}")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"[SUMMARY] Processed {df_transformed.shape[0]} rows")
    print(f"[SUMMARY] Output columns: {list(df_transformed.columns)}")
    print(f"[SUMMARY] Files saved to '{output_dir}/' directory")

if __name__ == "__main__":
    main()