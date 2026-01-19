import pandas as pd
import os
import sys

def main():
    # Define input and output paths
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
    
    # Check if 'narration' column exists (case-insensitive search)
    narration_col = None
    for col in df.columns:
        if col.lower() == 'narration':
            narration_col = col
            break
    
    if narration_col is None:
        print("\nWARNING: 'narration' column not found in the data!")
        print("Available columns:", list(df.columns))
        print("\nAttempting to extract bank names from any text columns that might contain bank information...")
        
        # Try to find any column that might contain bank-related information
        # Common bank name patterns
        bank_patterns = [
            r'(HDFC\s*BANK)',
            r'(ICICI\s*BANK)',
            r'(SBI|STATE\s*BANK\s*OF\s*INDIA)',
            r'(AXIS\s*BANK)',
            r'(KOTAK\s*MAHINDRA\s*BANK)',
            r'(YES\s*BANK)',
            r'(PUNJAB\s*NATIONAL\s*BANK|PNB)',
            r'(BANK\s*OF\s*BARODA|BOB)',
            r'(CANARA\s*BANK)',
            r'(UNION\s*BANK)',
            r'(IDBI\s*BANK)',
            r'(FEDERAL\s*BANK)',
            r'(INDUSIND\s*BANK)',
            r'(RBL\s*BANK)',
            r'(BANDHAN\s*BANK)',
            r'(\w+\s*BANK)',  # Generic pattern for any word followed by BANK
        ]
        
        # Create Bank_Name column with None values initially
        df['Bank_Name'] = None
        
        # Search through all string columns for bank names
        for col in df.columns:
            if df[col].dtype == 'object':
                for idx, value in df[col].items():
                    if pd.notna(value) and isinstance(value, str):
                        value_upper = value.upper()
                        for pattern in bank_patterns:
                            import re
                            match = re.search(pattern, value_upper, re.IGNORECASE)
                            if match:
                                if pd.isna(df.at[idx, 'Bank_Name']):
                                    df.at[idx, 'Bank_Name'] = match.group(1).strip()
                                break
        
        print("Created 'Bank_Name' column by searching all text columns for bank names.")
    else:
        print(f"\nFound narration column: '{narration_col}'")
        print("Extracting bank names from narration column...")
        
        # Define common bank name patterns to extract
        import re
        
        def extract_bank_name(narration):
            if pd.isna(narration) or not isinstance(narration, str):
                return None
            
            narration_upper = narration.upper()
            
            # List of bank patterns (ordered from specific to generic)
            bank_patterns = [
                (r'HDFC\s*BANK', 'HDFC BANK'),
                (r'ICICI\s*BANK', 'ICICI BANK'),
                (r'STATE\s*BANK\s*OF\s*INDIA', 'STATE BANK OF INDIA'),
                (r'\bSBI\b', 'SBI'),
                (r'AXIS\s*BANK', 'AXIS BANK'),
                (r'KOTAK\s*MAHINDRA\s*BANK', 'KOTAK MAHINDRA BANK'),
                (r'KOTAK\s*BANK', 'KOTAK BANK'),
                (r'YES\s*BANK', 'YES BANK'),
                (r'PUNJAB\s*NATIONAL\s*BANK', 'PUNJAB NATIONAL BANK'),
                (r'\bPNB\b', 'PNB'),
                (r'BANK\s*OF\s*BARODA', 'BANK OF BARODA'),
                (r'\bBOB\b', 'BOB'),
                (r'CANARA\s*BANK', 'CANARA BANK'),
                (r'UNION\s*BANK', 'UNION BANK'),
                (r'IDBI\s*BANK', 'IDBI BANK'),
                (r'FEDERAL\s*BANK', 'FEDERAL BANK'),
                (r'INDUSIND\s*BANK', 'INDUSIND BANK'),
                (r'RBL\s*BANK', 'RBL BANK'),
                (r'BANDHAN\s*BANK', 'BANDHAN BANK'),
                (r'CENTRAL\s*BANK', 'CENTRAL BANK'),
                (r'INDIAN\s*BANK', 'INDIAN BANK'),
                (r'INDIAN\s*OVERSEAS\s*BANK', 'INDIAN OVERSEAS BANK'),
                (r'UCO\s*BANK', 'UCO BANK'),
                (r'SYNDICATE\s*BANK', 'SYNDICATE BANK'),
                (r'ALLAHABAD\s*BANK', 'ALLAHABAD BANK'),
                (r'ANDHRA\s*BANK', 'ANDHRA BANK'),
                (r'CORPORATION\s*BANK', 'CORPORATION BANK'),
                (r'DENA\s*BANK', 'DENA BANK'),
                (r'VIJAYA\s*BANK', 'VIJAYA BANK'),
                (r'ORIENTAL\s*BANK', 'ORIENTAL BANK'),
                (r'(\w+)\s+BANK', None),  # Generic pattern - capture word before BANK
            ]
            
            for pattern, bank_name in bank_patterns:
                match = re.search(pattern, narration_upper)
                if match:
                    if bank_name:
                        return bank_name
                    else:
                        # For generic pattern, return the matched group
                        return match.group(0).strip()
            
            return None
        
        # Apply the extraction function
        df['Bank_Name'] = df[narration_col].apply(extract_bank_name)
        
        # Count extracted bank names
        extracted_count = df['Bank_Name'].notna().sum()
        print(f"Successfully extracted bank names from {extracted_count} out of {len(df)} rows")
    
    # Display transformed data
    print("\n" + "-" * 40)
    print("TRANSFORMED DATA PREVIEW:")
    print("-" * 40)
    print(df.head(10))
    
    # Show Bank_Name distribution
    print("\n" + "-" * 40)
    print("BANK NAME DISTRIBUTION:")
    print("-" * 40)
    print(df['Bank_Name'].value_counts(dropna=False))
    
    # Save to Excel
    print(f"\nSaving results to Excel: {output_xlsx}")
    try:
        df.to_excel(output_xlsx, index=False)
        print("Excel file saved successfully!")
    except Exception as e:
        print(f"ERROR saving Excel file: {e}")
    
    # Save to JSON
    print(f"Saving results to JSON: {output_json}")
    try:
        df.to_json(output_json, orient='records', indent=2)
        print("JSON file saved successfully!")
    except Exception as e:
        print(f"ERROR saving JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Total rows processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"Output columns: {list(df.columns)}")
    print(f"Bank names extracted: {df['Bank_Name'].notna().sum()}")
    print(f"Rows without bank name: {df['Bank_Name'].isna().sum()}")

if __name__ == "__main__":
    main()