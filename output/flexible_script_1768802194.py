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
    
    # Task: Standardize all transaction_date values to DD-MM-YYYY format
    # Note: The schema shows columns: Employee_ID, Department, Designation, Experience_Years, Location
    # There is no 'transaction_date' column in the schema, but we'll check for any date-like columns
    
    print("\n" + "-" * 40)
    print("TRANSFORMATION: Standardizing date columns to DD-MM-YYYY format")
    print("-" * 40)
    
    # Check if 'transaction_date' column exists
    date_columns_found = []
    
    if 'transaction_date' in df.columns:
        date_columns_found.append('transaction_date')
    
    # Also check for any other date-like columns (case-insensitive search)
    for col in df.columns:
        col_lower = col.lower()
        if 'date' in col_lower or 'time' in col_lower:
            if col not in date_columns_found:
                date_columns_found.append(col)
    
    # If no date columns found, check all columns for date-like data
    if not date_columns_found:
        print("No column named 'transaction_date' found in the data.")
        print("Checking all columns for date-like values...")
        
        for col in df.columns:
            # Try to convert each column to datetime to see if it contains dates
            try:
                # Sample non-null values
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    # Try parsing as datetime
                    pd.to_datetime(sample, errors='raise')
                    date_columns_found.append(col)
                    print(f"  - Column '{col}' appears to contain date values")
            except (ValueError, TypeError):
                continue
    
    if date_columns_found:
        print(f"\nDate columns to transform: {date_columns_found}")
        
        for col in date_columns_found:
            print(f"\nProcessing column: '{col}'")
            original_values = df[col].head(5).tolist()
            print(f"  Original values (first 5): {original_values}")
            
            try:
                # Convert to datetime first
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Count null values after conversion
                null_count = df[col].isna().sum()
                if null_count > 0:
                    print(f"  WARNING: {null_count} values could not be parsed as dates")
                
                # Format to DD-MM-YYYY string format
                df[col] = df[col].dt.strftime('%d-%m-%Y')
                
                # Handle NaT values that become 'NaT' strings
                df[col] = df[col].replace('NaT', None)
                
                transformed_values = df[col].head(5).tolist()
                print(f"  Transformed values (first 5): {transformed_values}")
                print(f"  Successfully standardized '{col}' to DD-MM-YYYY format")
                
            except Exception as e:
                print(f"  ERROR transforming column '{col}': {e}")
    else:
        print("\nNo date columns found in the dataset.")
        print("Available columns are: " + ", ".join(df.columns))
        print("The data will be saved as-is without date transformation.")
    
    # Display transformed data
    print("\n" + "-" * 40)
    print("TRANSFORMED DATA PREVIEW:")
    print("-" * 40)
    print(df.head())
    
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
    print(f"Total columns: {len(df.columns)}")
    print(f"Output files saved to: {output_dir}/")

if __name__ == "__main__":
    main()