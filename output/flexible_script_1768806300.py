import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("STARTING TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Input file path
    input_file = 'temp_uploads/age_sample.xlsx'
    
    # Output directory
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[INFO] Loading Excel file: {input_file}")
    
    # First, let's check what sheets are available in the Excel file
    try:
        xl = pd.ExcelFile(input_file)
        sheet_names = xl.sheet_names
        print(f"[INFO] Available sheets in the Excel file: {sheet_names}")
    except Exception as e:
        print(f"[ERROR] Failed to read Excel file: {e}")
        sys.exit(1)
    
    # Check if required sheets exist
    report_metadata_sheet = None
    ledger_master_sheet = None
    
    # Look for report_metadata sheet (case-insensitive)
    for sheet in sheet_names:
        if 'report_metadata' in sheet.lower():
            report_metadata_sheet = sheet
        if 'ledger_master' in sheet.lower():
            ledger_master_sheet = sheet
    
    # If specific sheets don't exist, we'll work with what we have
    if report_metadata_sheet is None or ledger_master_sheet is None:
        print(f"[WARNING] Could not find 'report_metadata' and/or 'ledger_master' sheets.")
        print(f"[INFO] Available sheets: {sheet_names}")
        
        # If there's only one sheet or the expected sheets don't exist,
        # we'll load all sheets and try to work with them
        all_sheets = {}
        for sheet in sheet_names:
            all_sheets[sheet] = pd.read_excel(input_file, sheet_name=sheet)
            print(f"[INFO] Loaded sheet '{sheet}' with {len(all_sheets[sheet])} rows and columns: {list(all_sheets[sheet].columns)}")
        
        # If we only have one sheet, just output it as-is with a note
        if len(sheet_names) == 1:
            print(f"[INFO] Only one sheet found. Cannot perform the requested transformation.")
            print(f"[INFO] Outputting the data as-is.")
            df = all_sheets[sheet_names[0]]
            
            # Save outputs
            output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
            output_json = os.path.join(output_dir, 'flexible_transform_result.json')
            
            df.to_excel(output_xlsx, index=False)
            print(f"[SUCCESS] Saved Excel output to: {output_xlsx}")
            
            df.to_json(output_json, orient='records', indent=2, date_format='iso')
            print(f"[SUCCESS] Saved JSON output to: {output_json}")
            
            print("\n" + "=" * 60)
            print("TRANSFORMATION COMPLETE")
            print("=" * 60)
            return
    else:
        print(f"[INFO] Found report_metadata sheet: '{report_metadata_sheet}'")
        print(f"[INFO] Found ledger_master sheet: '{ledger_master_sheet}'")
    
    # Load the sheets
    try:
        df_metadata = pd.read_excel(input_file, sheet_name=report_metadata_sheet)
        df_ledger = pd.read_excel(input_file, sheet_name=ledger_master_sheet)
        
        print(f"\n[INFO] report_metadata sheet:")
        print(f"       Rows: {len(df_metadata)}, Columns: {list(df_metadata.columns)}")
        print(f"[INFO] ledger_master sheet:")
        print(f"       Rows: {len(df_ledger)}, Columns: {list(df_ledger.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load sheets: {e}")
        sys.exit(1)
    
    # Extract period_start and period_end from report_metadata
    print("\n[INFO] Extracting period_start and period_end from report_metadata...")
    
    period_start = None
    period_end = None
    
    # Try to find period start and period end values
    # They might be in columns or as key-value pairs in rows
    
    # Check if columns exist directly
    metadata_cols_lower = {col.lower().replace(' ', '_').replace('-', '_'): col for col in df_metadata.columns}
    
    if 'period_start' in metadata_cols_lower:
        period_start = df_metadata[metadata_cols_lower['period_start']].iloc[0]
    elif 'periodstart' in metadata_cols_lower:
        period_start = df_metadata[metadata_cols_lower['periodstart']].iloc[0]
    elif 'period start' in [col.lower() for col in df_metadata.columns]:
        for col in df_metadata.columns:
            if col.lower() == 'period start':
                period_start = df_metadata[col].iloc[0]
                break
    
    if 'period_end' in metadata_cols_lower:
        period_end = df_metadata[metadata_cols_lower['period_end']].iloc[0]
    elif 'periodend' in metadata_cols_lower:
        period_end = df_metadata[metadata_cols_lower['periodend']].iloc[0]
    elif 'period end' in [col.lower() for col in df_metadata.columns]:
        for col in df_metadata.columns:
            if col.lower() == 'period end':
                period_end = df_metadata[col].iloc[0]
                break
    
    # If not found as columns, check if it's a key-value structure
    if period_start is None or period_end is None:
        print("[INFO] Checking for key-value structure in metadata...")
        # Look for a column that might contain keys like 'period_start', 'period_end'
        for col in df_metadata.columns:
            col_values = df_metadata[col].astype(str).str.lower().str.strip()
            
            if period_start is None:
                mask = col_values.str.contains('period.?start', regex=True, na=False)
                if mask.any():
                    idx = mask.idxmax()
                    # Get the value from the next column
                    col_idx = df_metadata.columns.get_loc(col)
                    if col_idx + 1 < len(df_metadata.columns):
                        period_start = df_metadata.iloc[idx, col_idx + 1]
            
            if period_end is None:
                mask = col_values.str.contains('period.?end', regex=True, na=False)
                if mask.any():
                    idx = mask.idxmax()
                    col_idx = df_metadata.columns.get_loc(col)
                    if col_idx + 1 < len(df_metadata.columns):
                        period_end = df_metadata.iloc[idx, col_idx + 1]
    
    print(f"[INFO] Extracted period_start: {period_start}")
    print(f"[INFO] Extracted period_end: {period_end}")
    
    # Add the new columns to ledger_master
    print("\n[INFO] Adding period_start and period_end columns to ledger_master...")
    df_ledger['period_start'] = period_start
    df_ledger['period_end'] = period_end
    
    print(f"[INFO] Updated ledger_master columns: {list(df_ledger.columns)}")
    print(f"[INFO] Sample of updated data:")
    print(df_ledger.head())
    
    # Save outputs
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Save to Excel - include both sheets, with ledger_master updated
    print(f"\n[INFO] Saving results...")
    
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        df_ledger.to_excel(writer, sheet_name='ledger_master', index=False)
        df_metadata.to_excel(writer, sheet_name='report_metadata', index=False)
    
    print(f"[SUCCESS] Saved Excel output to: {output_xlsx}")
    
    # Save ledger_master to JSON (the main transformed data)
    df_ledger.to_json(output_json, orient='records', indent=2, date_format='iso')
    print(f"[SUCCESS] Saved JSON output to: {output_json}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Added 'period_start' column with value: {period_start}")
    print(f"  - Added 'period_end' column with value: {period_end}")
    print(f"  - Output rows: {len(df_ledger)}")
    print(f"  - Output columns: {len(df_ledger.columns)}")

if __name__ == "__main__":
    main()