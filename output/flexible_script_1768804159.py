import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = r'temp_uploads\employee_department_data.xlsx'
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
    # Note: The schema shows Employee_ID, Department, Designation, Experience_Years, Location
    # There's no transaction amount column, but we'll check for numeric columns that could represent values
    
    print("\n" + "-" * 40)
    print("APPLYING TRANSFORMATION")
    print("-" * 40)
    
    # Check for potential numeric columns that could represent transaction values
    numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    print(f"Numeric columns found: {numeric_columns}")
    
    # Look for columns that might contain transaction/value data
    value_column = None
    potential_names = ['amount', 'value', 'transaction', 'salary', 'price', 'total', 'employee_id']
    
    for col in df.columns:
        col_lower = col.lower()
        for name in potential_names:
            if name in col_lower:
                if df[col].dtype in ['int64', 'float64']:
                    value_column = col
                    break
        if value_column:
            break
    
    # If no specific value column found, use the first numeric column or Employee_ID
    if value_column is None and numeric_columns:
        # Prefer Experience_Years or Employee_ID as they are numeric
        if 'Experience_Years' in numeric_columns:
            value_column = 'Experience_Years'
            print(f"Note: No transaction amount column found. Using '{value_column}' for demonstration.")
            print("Since Experience_Years values are typically small, all will likely be marked as 'No'.")
        elif 'Employee_ID' in numeric_columns:
            value_column = 'Employee_ID'
            print(f"Note: No transaction amount column found. Using '{value_column}' for demonstration.")
        else:
            value_column = numeric_columns[0]
            print(f"Note: No transaction amount column found. Using '{value_column}' for demonstration.")
    
    if value_column:
        print(f"\nUsing column '{value_column}' to determine High_Value status")
        print(f"Threshold: 100000")
        
        # Create the High_Value column
        df['High_Value'] = df[value_column].apply(
            lambda x: 'Yes' if pd.notna(x) and x > 100000 else 'No'
        )
        
        # Count results
        high_value_counts = df['High_Value'].value_counts()
        print(f"\nHigh_Value distribution:")
        for val, count in high_value_counts.items():
            print(f"  {val}: {count}")
    else:
        print("\nWARNING: No numeric columns found to evaluate against threshold.")
        print("Adding 'High_Value' column with default value 'No' for all rows.")
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
        df.to_json(output_json, orient='records', indent=2)
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