import pandas as pd
import os
import sys

def main():
    # Define input and output paths
    input_path = r'temp_uploads\sample_customer_data.xlsx'
    output_dir = 'output'
    output_excel = os.path.join(output_dir, 'flexible_transform_result.xlsx')
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
        print(f"[INFO] Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"[INFO] Columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display original data info
    print("\n[INFO] Original Data Preview:")
    print(df.head())
    
    # Check if 'Age' column exists
    if 'Age' not in df.columns:
        print(f"[ERROR] 'Age' column not found in the data. Available columns: {list(df.columns)}")
        sys.exit(1)
    
    print("\n[INFO] Creating 'Category' column based on Age...")
    print("[INFO] Rule: Age >= 40 -> 'Senior', Age < 40 -> 'Adult'")
    
    # Create the Category column
    # Handle potential null values in Age column
    def categorize_age(age):
        if pd.isna(age):
            return 'Unknown'
        elif age >= 40:
            return 'Senior'
        else:
            return 'Adult'
    
    df['Category'] = df['Age'].apply(categorize_age)
    
    # Log the categorization results
    category_counts = df['Category'].value_counts()
    print("\n[INFO] Category Distribution:")
    for category, count in category_counts.items():
        print(f"       - {category}: {count}")
    
    # Display transformed data preview
    print("\n[INFO] Transformed Data Preview:")
    print(df.head(10))
    
    # Save to Excel
    print(f"\n[INFO] Saving to Excel: {output_excel}")
    try:
        df.to_excel(output_excel, index=False, engine='openpyxl')
        print(f"[SUCCESS] Excel file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    print(f"\n[INFO] Saving to JSON: {output_json}")
    try:
        df.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"[SUCCESS] JSON file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - Excel: {output_excel}")
    print(f"  - JSON:  {output_json}")
    print(f"\nTotal records processed: {len(df)}")

if __name__ == "__main__":
    main()