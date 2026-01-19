import pandas as pd
import os
import sys

def main():
    # Define input and output paths
    input_path = r'temp_uploads\sample_customer_data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    print("=" * 60)
    print("STARTING DATA TRANSFORMATION")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] Created output directory: {output_dir}")
    
    # Load the Excel file
    print(f"\n[INFO] Loading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] File loaded successfully!")
        print(f"[INFO] Original data shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"[INFO] Columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display original data summary
    print("\n[INFO] Original data preview:")
    print(df.head())
    
    # Apply the filter: Gender is Female AND Age > 25
    print("\n[INFO] Applying filter: Gender == 'Female' AND Age > 25")
    
    # Check if required columns exist
    if 'Gender' not in df.columns:
        print("[ERROR] Column 'Gender' not found in the data!")
        sys.exit(1)
    if 'Age' not in df.columns:
        print("[ERROR] Column 'Age' not found in the data!")
        sys.exit(1)
    
    # Handle potential null values and apply filter
    # Convert Age to numeric in case it's stored as string
    df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
    
    # Apply the filter
    filtered_df = df[(df['Gender'].str.strip().str.lower() == 'female') & (df['Age'] > 25)]
    
    print(f"[SUCCESS] Filter applied successfully!")
    print(f"[INFO] Filtered data shape: {filtered_df.shape[0]} rows x {filtered_df.shape[1]} columns")
    
    if filtered_df.empty:
        print("[WARNING] No rows match the filter criteria!")
    else:
        print("\n[INFO] Filtered data preview:")
        print(filtered_df)
    
    # Save to Excel
    print(f"\n[INFO] Saving results to Excel: {output_xlsx}")
    try:
        filtered_df.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"[SUCCESS] Excel file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    print(f"\n[INFO] Saving results to JSON: {output_json}")
    try:
        filtered_df.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"[SUCCESS] JSON file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"[SUMMARY] Original rows: {df.shape[0]}")
    print(f"[SUMMARY] Filtered rows: {filtered_df.shape[0]}")
    print(f"[SUMMARY] Rows removed: {df.shape[0] - filtered_df.shape[0]}")
    print(f"[SUMMARY] Output files:")
    print(f"         - {output_xlsx}")
    print(f"         - {output_json}")
    print("=" * 60)

if __name__ == "__main__":
    main()