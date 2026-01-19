import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = 'temp_uploads/Corrected_Final_Data.xlsx'
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
    print(f"[INFO] Loading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] Loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"[INFO] Columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display initial data info
    print("\n[INFO] Initial data preview:")
    print(df.head(3).to_string())
    print(f"\n[INFO] Data types:\n{df.dtypes}")
    
    # Define what constitutes a "complete profile"
    # A complete profile has all key fields filled (non-null and non-empty)
    # Key fields: Industry, Type, Item_Name, Primary_Link, Secondary_Link, Whatsapp, Email
    
    print("\n[INFO] Adding 'Customer_Type' column based on profile completeness...")
    
    # Define the columns to check for completeness
    profile_columns = ['Industry', 'Type', 'Item_Name', 'Primary_Link', 'Secondary_Link', 'Whatsapp', 'Email']
    
    # Check which columns actually exist in the dataframe
    existing_columns = [col for col in profile_columns if col in df.columns]
    missing_columns = [col for col in profile_columns if col not in df.columns]
    
    if missing_columns:
        print(f"[WARNING] Some expected columns are missing: {missing_columns}")
    
    print(f"[INFO] Checking completeness based on columns: {existing_columns}")
    
    # Function to check if a row has a complete profile
    def is_complete_profile(row):
        for col in existing_columns:
            value = row[col]
            # Check if value is null, NaN, or empty string
            if pd.isna(value):
                return False
            if isinstance(value, str) and value.strip() == '':
                return False
        return True
    
    # Apply the function to create the Customer_Type column
    df['Customer_Type'] = df.apply(
        lambda row: 'Premium' if is_complete_profile(row) else 'Standard',
        axis=1
    )
    
    # Count the results
    premium_count = (df['Customer_Type'] == 'Premium').sum()
    standard_count = (df['Customer_Type'] == 'Standard').sum()
    
    print(f"\n[INFO] Customer Type Distribution:")
    print(f"       - Premium (complete profiles): {premium_count}")
    print(f"       - Standard (incomplete profiles): {standard_count}")
    
    # Show some examples of each type
    print("\n[INFO] Sample Premium customers:")
    premium_sample = df[df['Customer_Type'] == 'Premium'].head(2)
    if len(premium_sample) > 0:
        print(premium_sample.to_string())
    else:
        print("       No Premium customers found")
    
    print("\n[INFO] Sample Standard customers:")
    standard_sample = df[df['Customer_Type'] == 'Standard'].head(2)
    if len(standard_sample) > 0:
        print(standard_sample.to_string())
    else:
        print("       No Standard customers found")
    
    # Save to Excel
    print(f"\n[INFO] Saving results to Excel: {output_xlsx}")
    try:
        df.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"[SUCCESS] Excel file saved successfully")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    print(f"[INFO] Saving results to JSON: {output_json}")
    try:
        df.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"[SUCCESS] JSON file saved successfully")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"[SUMMARY] Total rows processed: {len(df)}")
    print(f"[SUMMARY] Total columns in output: {len(df.columns)}")
    print(f"[SUMMARY] New column added: 'Customer_Type'")
    print(f"[SUMMARY] Output files:")
    print(f"          - {output_xlsx}")
    print(f"          - {output_json}")
    print("=" * 60)

if __name__ == "__main__":
    main()