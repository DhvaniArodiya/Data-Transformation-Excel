import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = 'temp_uploads/employee_mixed_data.xlsx'
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
    
    # Display initial data info
    print("\n" + "-" * 40)
    print("INITIAL DATA PREVIEW:")
    print("-" * 40)
    print(df.head())
    print(f"\nData types:\n{df.dtypes}")
    
    # Task: Add a column "High_Value" that marks transactions above 100000 as "Yes" and others as "No"
    # Since this is employee data with Salary column, we'll use Salary as the value to check
    print("\n" + "-" * 40)
    print("APPLYING TRANSFORMATION")
    print("-" * 40)
    
    # Check which column to use for the threshold comparison
    # The task mentions "transactions above 100000" - in this employee data, Salary is the numeric value
    value_column = None
    
    # Look for potential value columns
    if 'Salary' in df.columns:
        value_column = 'Salary'
    elif 'Amount' in df.columns:
        value_column = 'Amount'
    elif 'Transaction_Amount' in df.columns:
        value_column = 'Transaction_Amount'
    elif 'Value' in df.columns:
        value_column = 'Value'
    
    if value_column:
        print(f"Using '{value_column}' column for High_Value determination (threshold: 100000)")
        
        # Convert to numeric if needed, handling any non-numeric values
        df[value_column] = pd.to_numeric(df[value_column], errors='coerce')
        
        # Add the High_Value column
        df['High_Value'] = df[value_column].apply(
            lambda x: 'Yes' if pd.notna(x) and x > 100000 else 'No'
        )
        
        # Count statistics
        high_value_count = (df['High_Value'] == 'Yes').sum()
        low_value_count = (df['High_Value'] == 'No').sum()
        
        print(f"High Value (>100000): {high_value_count} records")
        print(f"Not High Value (<=100000): {low_value_count} records")
    else:
        # If no suitable numeric column found, create the column with 'No' as default
        print("WARNING: No suitable numeric column found for threshold comparison.")
        print("Available columns:", list(df.columns))
        print("Creating 'High_Value' column with 'No' as default value.")
        df['High_Value'] = 'No'
    
    # Display transformed data preview
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
    print(f"Total records processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"Output columns: {list(df.columns)}")

if __name__ == "__main__":
    main()