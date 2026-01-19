import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = r'temp_uploads\Sample_data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    print("=" * 60)
    print("STARTING DATA TRANSFORMATION")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load the Excel file
    print(f"\nLoading data from: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns found: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Display original data info
    print("\n" + "-" * 40)
    print("ORIGINAL DATA PREVIEW:")
    print("-" * 40)
    print(df.head())
    print(f"\nData types:\n{df.dtypes}")
    
    # Task: Add a column "High_Value" that marks transactions above 100000 as "Yes" and others as "No"
    print("\n" + "-" * 40)
    print("APPLYING TRANSFORMATION")
    print("-" * 40)
    print("Task: Add 'High_Value' column marking transactions above 100000 as 'Yes', others as 'No'")
    
    # Look for a numeric column that could represent transaction values
    # Common column names for transaction amounts
    potential_value_columns = ['amount', 'value', 'transaction_amount', 'total', 'price', 
                               'ledger_amount', 'balance', 'transaction_value']
    
    # Find numeric columns in the dataframe
    numeric_columns = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
    print(f"\nNumeric columns found: {numeric_columns}")
    
    # Try to find the most appropriate column for transaction values
    value_column = None
    
    # First, check if any column name matches our potential value columns (case-insensitive)
    for col in df.columns:
        if col.lower() in [p.lower() for p in potential_value_columns]:
            value_column = col
            break
    
    # If not found, use the first numeric column (excluding ID columns)
    if value_column is None and numeric_columns:
        for col in numeric_columns:
            if 'id' not in col.lower():
                value_column = col
                break
        # If all numeric columns have 'id', just use the first numeric column
        if value_column is None:
            value_column = numeric_columns[0]
    
    if value_column is not None:
        print(f"Using column '{value_column}' for High_Value determination")
        
        # Convert to numeric, handling any non-numeric values
        df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
        
        # Add the High_Value column
        df['High_Value'] = df[value_column].apply(
            lambda x: 'Yes' if pd.notna(x) and x > 100000 else 'No'
        )
        
        # Count results
        high_value_count = (df['High_Value'] == 'Yes').sum()
        low_value_count = (df['High_Value'] == 'No').sum()
        print(f"\nHigh Value (>100000) transactions: {high_value_count}")
        print(f"Other transactions: {low_value_count}")
    else:
        print("\nWARNING: No suitable numeric column found for transaction values.")
        print("Adding 'High_Value' column with default value 'No' for all rows.")
        print("Available columns:", list(df.columns))
        df['High_Value'] = 'No'
    
    # Display transformed data
    print("\n" + "-" * 40)
    print("TRANSFORMED DATA PREVIEW:")
    print("-" * 40)
    print(df.head(10))
    
    # Save to Excel
    print("\n" + "-" * 40)
    print("SAVING OUTPUT FILES")
    print("-" * 40)
    
    try:
        df.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"Successfully saved Excel file: {output_xlsx}")
    except Exception as e:
        print(f"ERROR saving Excel file: {e}")
    
    # Save to JSON
    try:
        df.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"Successfully saved JSON file: {output_json}")
    except Exception as e:
        print(f"ERROR saving JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Total rows processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"Output columns: {list(df.columns)}")

if __name__ == "__main__":
    main()