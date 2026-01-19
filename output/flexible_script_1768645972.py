import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = r'temp_uploads\Sample_data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load the Excel file
    print(f"Loading data from: {input_path}")
    df = pd.read_excel(input_path)
    print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
    print(f"Original columns: {list(df.columns)}")
    
    # Display original data
    print("\nOriginal data preview:")
    print(df.head())
    
    # Check if 'address' column exists
    if 'address' not in df.columns:
        print("ERROR: 'address' column not found in the data!")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)
    
    print("\nSplitting 'address' column into 'Street', 'Area', and 'City_Address'...")
    
    # Split the address column
    # Assuming address is separated by commas or other delimiters
    # We'll try to split by comma first, then handle edge cases
    
    def split_address(address):
        """Split address into Street, Area, and City_Address components"""
        if pd.isna(address) or address == '':
            return pd.Series(['', '', ''])
        
        # Convert to string if not already
        address_str = str(address).strip()
        
        # Try splitting by comma
        parts = [p.strip() for p in address_str.split(',')]
        
        # Handle different number of parts
        if len(parts) >= 3:
            # If 3 or more parts, take first as Street, second as Area, rest as City_Address
            street = parts[0]
            area = parts[1]
            city_address = ', '.join(parts[2:])
        elif len(parts) == 2:
            # If 2 parts, first is Street, second is Area, City_Address is empty
            street = parts[0]
            area = parts[1]
            city_address = ''
        elif len(parts) == 1:
            # If only 1 part, put it in Street, others empty
            street = parts[0]
            area = ''
            city_address = ''
        else:
            street = ''
            area = ''
            city_address = ''
        
        return pd.Series([street, area, city_address])
    
    # Apply the split function
    df[['Street', 'Area', 'City_Address']] = df['address'].apply(split_address)
    
    print("Address column successfully split!")
    print(f"\nNew columns added: 'Street', 'Area', 'City_Address'")
    print(f"Updated columns: {list(df.columns)}")
    
    # Display transformed data
    print("\nTransformed data preview:")
    print(df.head())
    
    # Show the split results for verification
    print("\nAddress split results:")
    print(df[['address', 'Street', 'Area', 'City_Address']])
    
    # Save to Excel
    print(f"\nSaving to Excel: {output_xlsx}")
    df.to_excel(output_xlsx, index=False)
    print(f"Successfully saved Excel file!")
    
    # Save to JSON
    print(f"Saving to JSON: {output_json}")
    df.to_json(output_json, orient='records', indent=2)
    print(f"Successfully saved JSON file!")
    
    print("\n" + "="*50)
    print("TRANSFORMATION COMPLETE!")
    print(f"Total rows processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"Output files saved to: {output_dir}")
    print("="*50)

if __name__ == "__main__":
    main()