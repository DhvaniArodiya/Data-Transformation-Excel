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
    print(f"[INFO] Loading file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] File loaded successfully!")
        print(f"[INFO] Total rows: {len(df)}")
        print(f"[INFO] Columns found: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Task: Add "Profile_Status" column
    # The user wants to check for Name, Email, and Phone
    # However, the schema shows: Industry, Type, Item_Name, Primary_Link, Secondary_Link, Whatsapp, Email
    # We need to map the user's request to available columns:
    # - "Name" likely maps to "Item_Name"
    # - "Email" maps to "Email"
    # - "Phone" likely maps to "Whatsapp" (as there's no Phone column)
    
    print("\n[INFO] Adding 'Profile_Status' column...")
    print("[INFO] Mapping user request to available columns:")
    print("       - 'Name' -> 'Item_Name'")
    print("       - 'Email' -> 'Email'")
    print("       - 'Phone' -> 'Whatsapp' (closest match)")
    
    # Define the columns to check
    name_col = 'Item_Name' if 'Item_Name' in df.columns else None
    email_col = 'Email' if 'Email' in df.columns else None
    phone_col = 'Whatsapp' if 'Whatsapp' in df.columns else None
    
    # Check which columns are available
    available_cols = []
    if name_col:
        available_cols.append(name_col)
    if email_col:
        available_cols.append(email_col)
    if phone_col:
        available_cols.append(phone_col)
    
    print(f"[INFO] Columns being checked for completeness: {available_cols}")
    
    # Function to determine profile status
    def get_profile_status(row):
        # Check if all required fields are present and not null/empty
        name_present = False
        email_present = False
        phone_present = False
        
        if name_col and pd.notna(row.get(name_col)) and str(row.get(name_col)).strip() != '':
            name_present = True
        
        if email_col and pd.notna(row.get(email_col)) and str(row.get(email_col)).strip() != '':
            email_present = True
        
        if phone_col and pd.notna(row.get(phone_col)) and str(row.get(phone_col)).strip() != '':
            phone_present = True
        
        if name_present and email_present and phone_present:
            return "Complete"
        else:
            return "Incomplete"
    
    # Apply the function to create the new column
    df['Profile_Status'] = df.apply(get_profile_status, axis=1)
    
    # Count statistics
    complete_count = (df['Profile_Status'] == 'Complete').sum()
    incomplete_count = (df['Profile_Status'] == 'Incomplete').sum()
    
    print(f"\n[INFO] Profile Status Summary:")
    print(f"       - Complete: {complete_count}")
    print(f"       - Incomplete: {incomplete_count}")
    
    # Save to Excel
    print(f"\n[INFO] Saving to Excel: {output_xlsx}")
    try:
        df.to_excel(output_xlsx, index=False)
        print(f"[SUCCESS] Excel file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    print(f"[INFO] Saving to JSON: {output_json}")
    try:
        df.to_json(output_json, orient='records', indent=2)
        print(f"[SUCCESS] JSON file saved successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    # Display sample of the result
    print("\n[INFO] Sample of transformed data (first 5 rows):")
    print("-" * 60)
    print(df[['Item_Name', 'Email', 'Whatsapp', 'Profile_Status']].head().to_string())
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Output files:")
    print(f"  - {output_xlsx}")
    print(f"  - {output_json}")

if __name__ == "__main__":
    main()