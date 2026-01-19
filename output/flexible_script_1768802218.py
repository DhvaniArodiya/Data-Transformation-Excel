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
    
    # Task: Standardize all transaction_date values to DD-MM-YYYY format
    # Note: The schema shows columns: ledger_id, ledger_name, address, city, state
    # There is no 'transaction_date' column in the schema, but we'll check for it
    # and also check for any date-like columns
    
    print("\n" + "-" * 40)
    print("PROCESSING: Standardizing date values to DD-MM-YYYY format")
    print("-" * 40)
    
    # Check if 'transaction_date' column exists
    date_columns_processed = []
    
    if 'transaction_date' in df.columns:
        print(f"Found 'transaction_date' column - converting to DD-MM-YYYY format")
        try:
            # Convert to datetime first, then format as string
            df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
            df['transaction_date'] = df['transaction_date'].dt.strftime('%d-%m-%Y')
            # Replace 'NaT' string results with None/NaN
            df['transaction_date'] = df['transaction_date'].replace('NaT', None)
            date_columns_processed.append('transaction_date')
            print(f"Successfully converted 'transaction_date' to DD-MM-YYYY format")
        except Exception as e:
            print(f"Warning: Could not convert 'transaction_date': {e}")
    else:
        print("Note: 'transaction_date' column not found in the data")
        print("Searching for other date-like columns...")
        
        # Look for any columns that might contain dates
        for col in df.columns:
            col_lower = col.lower()
            # Check if column name suggests it's a date
            if any(date_term in col_lower for date_term in ['date', 'time', 'dt', 'created', 'updated', 'timestamp']):
                print(f"Found potential date column: '{col}'")
                try:
                    # Try to convert to datetime
                    temp_dates = pd.to_datetime(df[col], errors='coerce')
                    # Check if conversion was successful for at least some values
                    if temp_dates.notna().any():
                        df[col] = temp_dates.dt.strftime('%d-%m-%Y')
                        df[col] = df[col].replace('NaT', None)
                        date_columns_processed.append(col)
                        print(f"Successfully converted '{col}' to DD-MM-YYYY format")
                except Exception as e:
                    print(f"Could not convert '{col}': {e}")
            else:
                # Also check if the column contains date-like values
                if df[col].dtype == 'datetime64[ns]':
                    print(f"Found datetime column: '{col}'")
                    try:
                        df[col] = df[col].dt.strftime('%d-%m-%Y')
                        df[col] = df[col].replace('NaT', None)
                        date_columns_processed.append(col)
                        print(f"Successfully converted '{col}' to DD-MM-YYYY format")
                    except Exception as e:
                        print(f"Could not convert '{col}': {e}")
    
    if not date_columns_processed:
        print("\nNo date columns found to convert.")
        print("The data contains the following columns: " + ", ".join(df.columns))
        print("Proceeding with original data (no date transformation needed)")
    else:
        print(f"\nDate columns processed: {date_columns_processed}")
    
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