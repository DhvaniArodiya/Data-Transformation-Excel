import pandas as pd
import os
import sys

def main():
    # Define input and output paths
    input_path = 'temp_uploads/Sample_data.xlsx'
    output_dir = 'output'
    output_excel = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    print("=" * 60)
    print("DATA TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] Created output directory: {output_dir}")
    
    # Load the source Excel file
    print(f"\n[INFO] Loading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] File loaded successfully!")
        print(f"[INFO] Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"[INFO] Columns: {list(df.columns)}")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to load file: {str(e)}")
        sys.exit(1)
    
    # Display sample data
    print("\n[INFO] Sample data (first 5 rows):")
    print(df.head().to_string())
    
    # Check for any null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        print("\n[WARNING] Null values detected:")
        for col, count in null_counts.items():
            if count > 0:
                print(f"  - {col}: {count} null(s)")
    else:
        print("\n[INFO] No null values detected in the data.")
    
    # Save to JSON format
    print(f"\n[INFO] Converting to JSON format...")
    try:
        df.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"[SUCCESS] JSON file saved: {output_json}")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON: {str(e)}")
        sys.exit(1)
    
    # Save to Excel format
    print(f"\n[INFO] Converting to Excel format...")
    try:
        df.to_excel(output_excel, index=False, engine='openpyxl')
        print(f"[SUCCESS] Excel file saved: {output_excel}")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel: {str(e)}")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"[SUMMARY]")
    print(f"  - Input file: {input_path}")
    print(f"  - Records processed: {len(df)}")
    print(f"  - Columns: {len(df.columns)}")
    print(f"  - Output files:")
    print(f"    1. {output_json}")
    print(f"    2. {output_excel}")
    print("=" * 60)

if __name__ == "__main__":
    main()