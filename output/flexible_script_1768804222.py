import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = r'temp_uploads\Corrected_Final_Data.xlsx'
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
    print(f"[INFO] Loading file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] File loaded successfully!")
        print(f"[INFO] Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        print(f"[INFO] Columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display first few rows for context
    print("\n[INFO] Preview of original data:")
    print(df.head(3).to_string())
    
    # Task: Add a column "High_Value" that marks transactions above 100000 as "Yes" and others as "No"
    print("\n" + "=" * 60)
    print("APPLYING TRANSFORMATION")
    print("=" * 60)
    
    # Look for numeric columns that could represent transaction values
    numeric_columns = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
    print(f"[INFO] Numeric columns found: {numeric_columns}")
    
    # Check if there's a column that might contain transaction values
    # Common names for value columns
    value_column_candidates = ['value', 'amount', 'transaction', 'price', 'total', 'sum', 'cost']
    
    value_column = None
    for col in df.columns:
        col_lower = col.lower()
        for candidate in value_column_candidates:
            if candidate in col_lower:
                value_column = col
                break
        if value_column:
            break
    
    # If no obvious value column, check numeric columns
    if value_column is None and numeric_columns:
        value_column = numeric_columns[0]
        print(f"[INFO] No obvious value column found. Using first numeric column: '{value_column}'")
    
    if value_column is not None:
        print(f"[INFO] Using column '{value_column}' for High_Value classification")
        
        # Convert to numeric, handling any non-numeric values
        df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
        
        # Create the High_Value column
        df['High_Value'] = df[value_column].apply(
            lambda x: 'Yes' if pd.notna(x) and x > 100000 else 'No'
        )
        
        # Count results
        high_value_count = (df['High_Value'] == 'Yes').sum()
        low_value_count = (df['High_Value'] == 'No').sum()
        
        print(f"[INFO] High Value (>100000) transactions: {high_value_count}")
        print(f"[INFO] Other transactions: {low_value_count}")
    else:
        # No numeric column found - create column with all "No" values
        print("[WARNING] No numeric column found for transaction values.")
        print("[INFO] Creating 'High_Value' column with default 'No' values.")
        print("[INFO] If you have a specific column for values, please specify it.")
        df['High_Value'] = 'No'
    
    print(f"\n[INFO] New columns: {list(df.columns)}")
    
    # Display preview of transformed data
    print("\n[INFO] Preview of transformed data:")
    print(df.head(5).to_string())
    
    # Save to Excel
    print("\n" + "=" * 60)
    print("SAVING OUTPUT FILES")
    print("=" * 60)
    
    try:
        df.to_excel(output_xlsx, index=False)
        print(f"[SUCCESS] Saved Excel file: {output_xlsx}")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    try:
        df.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"[SUCCESS] Saved JSON file: {output_json}")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"[INFO] Total rows processed: {len(df)}")
    print(f"[INFO] Total columns in output: {len(df.columns)}")

if __name__ == "__main__":
    main()