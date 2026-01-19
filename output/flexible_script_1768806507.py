import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("EXCEL TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Input and output paths
    input_path = r'temp_uploads\Corrected_Final_Data.xlsx'
    output_dir = 'output'
    output_excel = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    print(f"\nLoading source file: {input_path}")
    
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
    metadata_sheet_names = ['report_metadata', 'Report_Metadata', 'ReportMetadata', 'metadata', 'Metadata']
    metadata_df = None
    
    for sheet_name in metadata_sheet_names:
        if sheet_name in available_sheets:
            print(f"\nFound metadata sheet: '{sheet_name}'")
            metadata_df = pd.read_excel(input_path, sheet_name=sheet_name)
            print(f"Metadata sheet columns: {metadata_df.columns.tolist()}")
            print(f"Metadata sheet preview:\n{metadata_df.head()}")
            break
    
    if metadata_df is not None:
        # Try to extract period start and end dates from metadata
        # Look for common column names or patterns
        for col in metadata_df.columns:
            col_lower = str(col).lower()
            if 'start' in col_lower and ('period' in col_lower or 'date' in col_lower):
                period_start = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                print(f"Found period start in column '{col}': {period_start}")
            elif 'end' in col_lower and ('period' in col_lower or 'date' in col_lower):
                period_end = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                print(f"Found period end in column '{col}': {period_end}")
        
        # If not found by column names, try to find in a key-value format
        if period_start is None or period_end is None:
            for idx, row in metadata_df.iterrows():
                for col in metadata_df.columns:
                    cell_value = str(row[col]).lower() if pd.notna(row[col]) else ''
                    if 'period' in cell_value and 'start' in cell_value:
                        # Look for the value in the next column or row
                        col_idx = metadata_df.columns.get_loc(col)
                        if col_idx + 1 < len(metadata_df.columns):
                            period_start = row[metadata_df.columns[col_idx + 1]]
                            print(f"Found period start date: {period_start}")
                    elif 'period' in cell_value and 'end' in cell_value:
                        col_idx = metadata_df.columns.get_loc(col)
                        if col_idx + 1 < len(metadata_df.columns):
                            period_end = row[metadata_df.columns[col_idx + 1]]
                            print(f"Found period end date: {period_end}")
    else:
        print("\nWARNING: No 'report_metadata' sheet found in the Excel file.")
        print("Setting default placeholder values for period dates.")
        period_start = "N/A - No metadata sheet found"
        period_end = "N/A - No metadata sheet found"
    
    # Try to find and read the ledger_master sheet
    ledger_sheet_names = ['ledger_master', 'Ledger_Master', 'LedgerMaster', 'ledger', 'Ledger', 'Sheet1']
    main_df = None
    used_sheet_name = None
    
    for sheet_name in ledger_sheet_names:
        if sheet_name in available_sheets:
            print(f"\nFound ledger sheet: '{sheet_name}'")
            main_df = pd.read_excel(input_path, sheet_name=sheet_name)
            used_sheet_name = sheet_name
            break
    
    # If no specific ledger sheet found, use the first sheet
    if main_df is None:
        print(f"\nNo specific ledger sheet found. Using first sheet: '{available_sheets[0]}'")
        main_df = pd.read_excel(input_path, sheet_name=available_sheets[0])
        used_sheet_name = available_sheets[0]
    
    print(f"\nOriginal data shape: {main_df.shape}")
    print(f"Original columns: {main_df.columns.tolist()}")
    
    # Add the period_start and period_end columns
    print("\nAdding 'period_start' and 'period_end' columns to the data...")
    
    # Handle None values
    if period_start is None:
        period_start = "Not specified"
    if period_end is None:
        period_end = "Not specified"
    
    main_df['period_start'] = period_start
    main_df['period_end'] = period_end
    
    print(f"Period Start Date: {period_start}")
    print(f"Period End Date: {period_end}")
    print(f"Updated data shape: {main_df.shape}")
    print(f"Updated columns: {main_df.columns.tolist()}")
    
    # Preview the updated data
    print("\nPreview of updated data:")
    print(main_df.head())
    
    # Save to Excel
    print(f"\nSaving to Excel: {output_excel}")
    try:
        main_df.to_excel(output_excel, index=False, sheet_name='ledger_master')
        print(f"Successfully saved Excel file: {output_excel}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")
    
    # Save to JSON
    print(f"\nSaving to JSON: {output_json}")
    try:
        # Convert datetime objects to strings for JSON serialization
        df_for_json = main_df.copy()
        for col in df_for_json.columns:
            if df_for_json[col].dtype == 'datetime64[ns]':
                df_for_json[col] = df_for_json[col].astype(str)
        
        df_for_json.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"Successfully saved JSON file: {output_json}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Total records processed: {len(main_df)}")
    print(f"Columns in output: {len(main_df.columns)}")
    print(f"New columns added: 'period_start', 'period_end'")
    print(f"Output files:")
    print(f"  - {output_excel}")
    print(f"  - {output_json}")

if __name__ == "__main__":
    main()