import pandas as pd
import os
import sys

def main():
    # Define input and output paths
    input_path = r'temp_uploads\Corrected_Final_Data.xlsx'
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
    
    # Display initial data info
    print("\n" + "-" * 40)
    print("INITIAL DATA PREVIEW:")
    print("-" * 40)
    print(df.head())
    
    # Task: Create "Is_Duplicate" column based on Email or Phone (Whatsapp)
    print("\n" + "-" * 40)
    print("PROCESSING: Creating 'Is_Duplicate' column")
    print("-" * 40)
    
    # Initialize Is_Duplicate column as False
    df['Is_Duplicate'] = False
    
    # Check for Email column
    email_col = None
    if 'Email' in df.columns:
        email_col = 'Email'
        print(f"Found Email column: '{email_col}'")
    
    # Check for Phone/Whatsapp column
    phone_col = None
    if 'Whatsapp' in df.columns:
        phone_col = 'Whatsapp'
        print(f"Found Phone/Whatsapp column: '{phone_col}'")
    elif 'Phone' in df.columns:
        phone_col = 'Phone'
        print(f"Found Phone column: '{phone_col}'")
    
    # Mark duplicates based on Email
    email_duplicates = 0
    if email_col:
        # Normalize email for comparison (lowercase, strip whitespace)
        df['_email_normalized'] = df[email_col].astype(str).str.lower().str.strip()
        # Replace empty strings and 'nan' with actual NaN
        df['_email_normalized'] = df['_email_normalized'].replace(['', 'nan', 'none'], pd.NA)
        
        # Find duplicates (mark all occurrences after the first as duplicates)
        email_dup_mask = df['_email_normalized'].notna() & df.duplicated(subset=['_email_normalized'], keep='first')
        email_duplicates = email_dup_mask.sum()
        df.loc[email_dup_mask, 'Is_Duplicate'] = True
        
        # Clean up temporary column
        df.drop('_email_normalized', axis=1, inplace=True)
        print(f"Found {email_duplicates} duplicate records based on Email")
    
    # Mark duplicates based on Phone/Whatsapp
    phone_duplicates = 0
    if phone_col:
        # Normalize phone for comparison (remove non-numeric characters, strip whitespace)
        df['_phone_normalized'] = df[phone_col].astype(str).str.replace(r'\D', '', regex=True).str.strip()
        # Replace empty strings and 'nan' with actual NaN
        df['_phone_normalized'] = df['_phone_normalized'].replace(['', 'nan', 'none'], pd.NA)
        
        # Find duplicates (mark all occurrences after the first as duplicates)
        # Only mark as duplicate if not already marked
        phone_dup_mask = df['_phone_normalized'].notna() & df.duplicated(subset=['_phone_normalized'], keep='first') & ~df['Is_Duplicate']
        phone_duplicates = phone_dup_mask.sum()
        df.loc[phone_dup_mask, 'Is_Duplicate'] = True
        
        # Clean up temporary column
        df.drop('_phone_normalized', axis=1, inplace=True)
        print(f"Found {phone_duplicates} additional duplicate records based on Phone/Whatsapp")
    
    # Summary
    total_duplicates = df['Is_Duplicate'].sum()
    print(f"\nTotal records marked as duplicates: {total_duplicates}")
    print(f"Total unique records: {len(df) - total_duplicates}")
    
    # Display duplicates if any
    if total_duplicates > 0:
        print("\n" + "-" * 40)
        print("DUPLICATE RECORDS:")
        print("-" * 40)
        print(df[df['Is_Duplicate'] == True])
    
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
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Input file: {input_path}")
    print(f"Output Excel: {output_xlsx}")
    print(f"Output JSON: {output_json}")
    print(f"Total rows processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"New column added: 'Is_Duplicate'")
    print(f"Duplicates found: {total_duplicates}")
    print("=" * 60)

if __name__ == "__main__":
    main()