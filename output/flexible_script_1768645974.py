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
    print(f"\nLoading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"Original columns: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Display original data sample
    print("\nOriginal data sample:")
    print(df.head())
    
    # Check if 'address' column exists
    if 'address' not in df.columns:
        print("\nERROR: 'address' column not found in the data!")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    print("\n" + "-" * 60)
    print("SPLITTING ADDRESS COLUMN")
    print("-" * 60)
    
    # Split the address column into Street, Area, and City_Address
    # Assuming address is comma-separated (e.g., "123 Main St, Downtown, New York")
    # We'll split by comma and handle cases with different number of parts
    
    def split_address(address):
        """Split address into Street, Area, and City_Address components"""
        if pd.isna(address) or address == '':
            return pd.Series(['', '', ''])
        
        # Convert to string and split by comma
        address_str = str(address).strip()
        parts = [part.strip() for part in address_str.split(',')]
        
        # Handle different number of parts
        if len(parts) >= 3:
            street = parts[0]
            area = parts[1]
            city_address = ', '.join(parts[2:])  # Join remaining parts as city
        elif len(parts) == 2:
            street = parts[0]
            area = parts[1]
            city_address = ''
        elif len(parts) == 1:
            street = parts[0]
            area = ''
            city_address = ''
        else:
            street = ''
            area = ''
            city_address = ''
        
        return pd.Series([street, area, city_address])
    
    # Apply the split function
    print("Splitting address into: Street, Area, City_Address")
    df[['Street', 'Area', 'City_Address']] = df['address'].apply(split_address)
    
    # Log the transformation
    print(f"\nNew columns added: Street, Area, City_Address")
    print(f"Total columns now: {len(df.columns)}")
    print(f"Updated columns: {list(df.columns)}")
    
    # Display transformed data sample
    print("\nTransformed data sample:")
    print(df[['address', 'Street', 'Area', 'City_Address']].head())
    
    # Display full transformed dataframe
    print("\nFull transformed data:")
    print(df.head(10))
    
    print("\n" + "-" * 60)
    print("SAVING OUTPUT FILES")
    print("-" * 60)
    
    # Save to Excel
    try:
        df.to_excel(output_xlsx, index=False)
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
    print(f"\nSummary:")
    print(f"  - Input rows: {len(df)}")
    print(f"  - Output rows: {len(df)}")
    print(f"  - Original columns: ledger_id, ledger_name, address, city, state")
    print(f"  - New columns added: Street, Area, City_Address")
    print(f"  - Output files:")
    print(f"    - {output_xlsx}")
    print(f"    - {output_json}")

if __name__ == "__main__":
    main()