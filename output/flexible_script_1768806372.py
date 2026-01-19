import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("EXCEL TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Input and output paths
    input_path = r'temp_uploads\employee_mixed_data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    print(f"\nLoading Excel file: {input_path}")
    
    # First, let's check what sheets are available in the Excel file
    try:
        xl_file = pd.ExcelFile(input_path)
        available_sheets = xl_file.sheet_names
        print(f"Available sheets in the file: {available_sheets}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)
    
    # Initialize variables for period dates
    period_start = None
    period_end = None
    
    # Try to find and read the report_metadata sheet
    metadata_sheet_name = None
    for sheet in available_sheets:
        if 'metadata' in sheet.lower() or 'report' in sheet.lower():
            metadata_sheet_name = sheet
            break
    
    if metadata_sheet_name:
        print(f"\nFound metadata sheet: {metadata_sheet_name}")
        try:
            metadata_df = pd.read_excel(input_path, sheet_name=metadata_sheet_name)
            print(f"Metadata sheet columns: {metadata_df.columns.tolist()}")
            print(f"Metadata sheet preview:\n{metadata_df.head()}")
            
            # Try to extract period start and end dates from metadata
            for col in metadata_df.columns:
                col_lower = col.lower()
                if 'start' in col_lower or 'begin' in col_lower:
                    period_start = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                elif 'end' in col_lower:
                    period_end = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
            
            # If not found in columns, check row values
            if period_start is None or period_end is None:
                for idx, row in metadata_df.iterrows():
                    for col in metadata_df.columns:
                        val = str(row[col]).lower() if pd.notna(row[col]) else ''
                        if 'start' in val or 'begin' in val:
                            # Look for date in adjacent columns or next row
                            pass
                        elif 'end' in val:
                            pass
                            
        except Exception as e:
            print(f"Error reading metadata sheet: {e}")
    else:
        print("\nNo 'report_metadata' sheet found in the file.")
    
    # Try to find and read the ledger_master sheet
    ledger_sheet_name = None
    for sheet in available_sheets:
        if 'ledger' in sheet.lower() or 'master' in sheet.lower():
            ledger_sheet_name = sheet
            break
    
    # If specific sheets not found, use the first/main sheet
    if ledger_sheet_name is None:
        ledger_sheet_name = available_sheets[0]
        print(f"\nNo 'ledger_master' sheet found. Using main sheet: {ledger_sheet_name}")
    else:
        print(f"\nFound ledger sheet: {ledger_sheet_name}")
    
    # Read the main data sheet
    try:
        main_df = pd.read_excel(input_path, sheet_name=ledger_sheet_name)
        print(f"\nMain data sheet columns: {main_df.columns.tolist()}")
        print(f"Total rows: {len(main_df)}")
    except Exception as e:
        print(f"Error reading main data sheet: {e}")
        sys.exit(1)
    
    # If period dates weren't found, set default values based on data
    if period_start is None:
        # Try to infer from Joining_Date column if it exists
        if 'Joining_Date' in main_df.columns:
            try:
                dates = pd.to_datetime(main_df['Joining_Date'], errors='coerce')
                period_start = dates.min()
                print(f"Inferred period_start from Joining_Date: {period_start}")
            except:
                period_start = pd.Timestamp('2024-01-01')
                print(f"Using default period_start: {period_start}")
        else:
            period_start = pd.Timestamp('2024-01-01')
            print(f"Using default period_start: {period_start}")
    
    if period_end is None:
        if 'Joining_Date' in main_df.columns:
            try:
                dates = pd.to_datetime(main_df['Joining_Date'], errors='coerce')
                period_end = dates.max()
                print(f"Inferred period_end from Joining_Date: {period_end}")
            except:
                period_end = pd.Timestamp('2024-12-31')
                print(f"Using default period_end: {period_end}")
        else:
            period_end = pd.Timestamp('2024-12-31')
            print(f"Using default period_end: {period_end}")
    
    # Add period_start and period_end columns to the main dataframe
    print(f"\nAdding 'period_start' column with value: {period_start}")
    print(f"Adding 'period_end' column with value: {period_end}")
    
    main_df['period_start'] = period_start
    main_df['period_end'] = period_end
    
    print(f"\nUpdated dataframe columns: {main_df.columns.tolist()}")
    print(f"\nPreview of updated data:")
    print(main_df.head(10).to_string())
    
    # Save to Excel
    print(f"\nSaving to Excel: {output_xlsx}")
    try:
        main_df.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"Successfully saved Excel file: {output_xlsx}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")
    
    # Save to JSON
    print(f"\nSaving to JSON: {output_json}")
    try:
        # Convert datetime columns to string for JSON serialization
        json_df = main_df.copy()
        for col in json_df.columns:
            if pd.api.types.is_datetime64_any_dtype(json_df[col]):
                json_df[col] = json_df[col].astype(str)
        
        json_df.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"Successfully saved JSON file: {output_json}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Output files:")
    print(f"  - {output_xlsx}")
    print(f"  - {output_json}")
    print(f"Total records processed: {len(main_df)}")

if __name__ == "__main__":
    main()