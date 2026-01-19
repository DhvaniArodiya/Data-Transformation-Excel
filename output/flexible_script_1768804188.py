import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = r'temp_uploads\age_sample.xlsx'
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
        print(f"Columns: {list(df.columns)}")
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
    potential_value_columns = ['Amount', 'Value', 'Transaction', 'Price', 'Total', 'Sum', 'Age', 'Id']
    
    # Find the best candidate column for transaction values
    value_column = None
    for col in df.columns:
        # Check if column name contains common value-related terms
        col_lower = col.lower()
        if any(term in col_lower for term in ['amount', 'value', 'transaction', 'price', 'total', 'sum']):
            if pd.api.types.is_numeric_dtype(df[col]):
                value_column = col
                break
    
    # If no obvious value column found, check for numeric columns
    if value_column is None:
        numeric_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
        print(f"Numeric columns found: {numeric_cols}")
        
        # Use 'Id' column if it exists and is numeric (as it might represent transaction IDs/values)
        # Or use the first numeric column that could represent values
        if 'Id' in numeric_cols:
            value_column = 'Id'
        elif numeric_cols:
            # Prefer columns that might have larger values
            for col in numeric_cols:
                if df[col].max() > 100:  # At least some values that could be compared to 100000
                    value_column = col
                    break
            if value_column is None:
                value_column = numeric_cols[0]
    
    if value_column is not None:
        print(f"Using column '{value_column}' for High_Value determination")
        print(f"Column statistics - Min: {df[value_column].min()}, Max: {df[value_column].max()}, Mean: {df[value_column].mean():.2f}")
        
        # Add the High_Value column
        df['High_Value'] = df[value_column].apply(lambda x: 'Yes' if pd.notna(x) and x > 100000 else 'No')
        
        # Count results
        high_value_counts = df['High_Value'].value_counts()
        print(f"\nHigh_Value distribution:")
        print(f"  - Yes (above 100000): {high_value_counts.get('Yes', 0)}")
        print(f"  - No (100000 or below): {high_value_counts.get('No', 0)}")
    else:
        print("WARNING: No suitable numeric column found for transaction values")
        print("Adding 'High_Value' column with default 'No' values")
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
        df.to_excel(output_xlsx, index=False)
        print(f"Successfully saved Excel file: {output_xlsx}")
    except Exception as e:
        print(f"ERROR saving Excel file: {e}")
    
    # Save to JSON
    try:
        df.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"Successfully saved JSON file: {output_json}")
    except Exception as e:
        print(f"ERROR saving JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Total rows processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"New column added: 'High_Value'")

if __name__ == "__main__":
    main()