import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = r'temp_uploads\Corrected_Final_Data.xlsx'
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
        print(f"[INFO] Total rows: {len(df)}")
        print(f"[INFO] Total columns: {len(df.columns)}")
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
    
    # Check for null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        print("\n[INFO] Null value counts per column:")
        for col, count in null_counts.items():
            if count > 0:
                print(f"  - {col}: {count} null values")
    else:
        print("\n[INFO] No null values detected in the dataset.")
    
    # Save to Excel format
    print(f"\n[INFO] Saving data to Excel format: {output_excel}")
    try:
        df.to_excel(output_excel, index=False, engine='openpyxl')
        print(f"[SUCCESS] Excel file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {str(e)}")
        sys.exit(1)
    
    # Save to JSON format
    print(f"\n[INFO] Saving data to JSON format: {output_json}")
    try:
        # Convert to JSON with proper formatting
        df.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"[SUCCESS] JSON file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {str(e)}")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"\n[SUMMARY]")
    print(f"  - Input file: {input_path}")
    print(f"  - Records processed: {len(df)}")
    print(f"  - Output Excel: {output_excel}")
    print(f"  - Output JSON: {output_json}")
    print("\n[INFO] Both files have been created successfully!")

if __name__ == "__main__":
    main()