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
    
    # Load the Excel file
    print(f"\nLoading data from: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Display original data
    print("\nOriginal Data Preview:")
    print(df.head(10).to_string())
    
    # Add the Transaction_Category column based on ledger_name
    print("\n" + "-" * 60)
    print("APPLYING TRANSFORMATION: Adding 'Transaction_Category' column")
    print("-" * 60)
    
    # Check if ledger_name column exists
    if 'ledger_name' not in df.columns:
        print("WARNING: 'ledger_name' column not found. Checking for similar columns...")
        # Try to find a similar column (case-insensitive)
        for col in df.columns:
            if 'ledger' in col.lower() and 'name' in col.lower():
                print(f"Found similar column: '{col}'. Using this column.")
                df.rename(columns={col: 'ledger_name'}, inplace=True)
                break
    
    # Define the categorization function
    def categorize_transaction(ledger_name):
        if pd.isna(ledger_name):
            return "Unknown"
        
        ledger_name_lower = str(ledger_name).lower().strip()
        
        # Check for Payment or Receipt -> Bank
        if 'payment' in ledger_name_lower or 'receipt' in ledger_name_lower:
            return "Bank"
        # Check for Purchase -> Expense
        elif 'purchase' in ledger_name_lower:
            return "Expense"
        # Check for Sales -> Income
        elif 'sale' in ledger_name_lower or 'sales' in ledger_name_lower:
            return "Income"
        else:
            return "Other"
    
    # Apply the categorization
    df['Transaction_Category'] = df['ledger_name'].apply(categorize_transaction)
    
    # Log the categorization results
    print("\nCategorization Summary:")
    category_counts = df['Transaction_Category'].value_counts()
    for category, count in category_counts.items():
        print(f"  - {category}: {count} records")
    
    # Display transformed data
    print("\nTransformed Data Preview:")
    print(df.head(10).to_string())
    
    # Save to Excel
    print("\n" + "-" * 60)
    print("SAVING OUTPUT FILES")
    print("-" * 60)
    
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
    print(f"Total records processed: {len(df)}")
    print(f"Output columns: {list(df.columns)}")

if __name__ == "__main__":
    main()