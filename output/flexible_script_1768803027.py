import pandas as pd
import os
import sys

def main():
    # Define input and output paths
    input_path = 'temp_uploads/Sample_data.xlsx'
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
    
    # Load the source file
    print(f"\nLoading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"Successfully loaded file with {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Display original data
    print("\nOriginal Data Preview:")
    print(df.head(10))
    
    # Add the Txn_Type column based on ledger_name
    print("\n" + "-" * 60)
    print("ADDING 'Txn_Type' COLUMN")
    print("-" * 60)
    
    # Define the mapping for transaction types
    txn_type_mapping = {
        'Opening Balance': 'Opening',
        'Payment': 'Outflow',
        'Receipt': 'Inflow',
        'Purchase': 'Expense'
    }
    
    print(f"Mapping rules:")
    for key, value in txn_type_mapping.items():
        print(f"  - '{key}' -> '{value}'")
    
    # Check if ledger_name column exists
    if 'ledger_name' not in df.columns:
        print("WARNING: 'ledger_name' column not found. Checking for similar columns...")
        # Try to find a similar column (case-insensitive)
        for col in df.columns:
            if 'ledger' in col.lower() and 'name' in col.lower():
                print(f"Found similar column: '{col}'. Using this column.")
                df['Txn_Type'] = df[col].map(txn_type_mapping)
                break
        else:
            print("No suitable column found. Creating Txn_Type with null values.")
            df['Txn_Type'] = None
    else:
        # Apply the mapping to create Txn_Type column
        df['Txn_Type'] = df['ledger_name'].map(txn_type_mapping)
    
    # Check for any unmapped values
    unmapped_mask = df['Txn_Type'].isna()
    if unmapped_mask.any():
        unmapped_values = df.loc[unmapped_mask, 'ledger_name'].unique()
        print(f"\nWARNING: Some ledger_name values were not mapped: {list(unmapped_values)}")
        print("These will have null/NaN in Txn_Type column")
    
    # Display transformation results
    print("\nTransformation Summary:")
    print(df['Txn_Type'].value_counts(dropna=False))
    
    # Display transformed data
    print("\nTransformed Data Preview:")
    print(df.head(10))
    
    # Save to Excel
    print("\n" + "-" * 60)
    print("SAVING OUTPUT FILES")
    print("-" * 60)
    
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
    print(f"New column added: 'Txn_Type'")
    print(f"Output files saved to: {output_dir}/")

if __name__ == "__main__":
    main()