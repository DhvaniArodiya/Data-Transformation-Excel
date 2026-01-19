import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = 'temp_uploads/employee_department_data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory ensured: {output_dir}")
    
    # Load the Excel file
    print(f"[INFO] Loading Excel file: {input_path}")
    
    try:
        # First, let's see what sheets are available
        xl = pd.ExcelFile(input_path)
        sheet_names = xl.sheet_names
        print(f"[INFO] Available sheets: {sheet_names}")
        
        # Look for report_metadata sheet (case-insensitive search)
        report_metadata_sheet = None
        ledger_master_sheet = None
        
        for sheet in sheet_names:
            if 'report_metadata' in sheet.lower() or 'metadata' in sheet.lower():
                report_metadata_sheet = sheet
            if 'ledger_master' in sheet.lower() or 'ledger' in sheet.lower():
                ledger_master_sheet = sheet
        
        # If specific sheets not found, try to work with available sheets
        if report_metadata_sheet is None or ledger_master_sheet is None:
            print(f"[WARNING] Could not find expected sheets 'report_metadata' and 'ledger_master'")
            print(f"[INFO] Available sheets are: {sheet_names}")
            
            # If there's only one sheet or we need to handle differently
            if len(sheet_names) == 1:
                print(f"[INFO] Only one sheet found: {sheet_names[0]}")
                # Load the single sheet
                df = pd.read_excel(input_path, sheet_name=sheet_names[0])
                print(f"[INFO] Loaded sheet with {len(df)} rows and columns: {list(df.columns)}")
                
                # Since we can't find the expected sheets, we'll add placeholder columns
                print("[WARNING] Cannot find report_metadata sheet to extract period values")
                print("[INFO] Adding placeholder period_start and period_end columns")
                df['period_start'] = None
                df['period_end'] = None
                
            elif len(sheet_names) >= 2:
                # Try to use first sheet as metadata and second as ledger
                print(f"[INFO] Attempting to use first sheet as metadata source and second as main data")
                
                # Load all sheets to inspect
                all_sheets = {}
                for sheet in sheet_names:
                    all_sheets[sheet] = pd.read_excel(input_path, sheet_name=sheet)
                    print(f"[INFO] Sheet '{sheet}': {len(all_sheets[sheet])} rows, columns: {list(all_sheets[sheet].columns)}")
                
                # Use the first sheet as main data
                df = all_sheets[sheet_names[0]]
                df['period_start'] = None
                df['period_end'] = None
                print("[INFO] Added placeholder period_start and period_end columns")
        else:
            # Found both sheets
            print(f"[INFO] Found report_metadata sheet: {report_metadata_sheet}")
            print(f"[INFO] Found ledger_master sheet: {ledger_master_sheet}")
            
            # Load both sheets
            df_metadata = pd.read_excel(input_path, sheet_name=report_metadata_sheet)
            df_ledger = pd.read_excel(input_path, sheet_name=ledger_master_sheet)
            
            print(f"[INFO] Metadata sheet columns: {list(df_metadata.columns)}")
            print(f"[INFO] Ledger sheet columns: {list(df_ledger.columns)}")
            print(f"[INFO] Ledger sheet rows: {len(df_ledger)}")
            
            # Extract period_start and period_end from metadata
            period_start = None
            period_end = None
            
            # Try to find period values - could be in columns or rows
            for col in df_metadata.columns:
                col_lower = str(col).lower()
                if 'period_start' in col_lower or 'period start' in col_lower or 'start' in col_lower:
                    period_start = df_metadata[col].iloc[0] if len(df_metadata) > 0 else None
                if 'period_end' in col_lower or 'period end' in col_lower or 'end' in col_lower:
                    period_end = df_metadata[col].iloc[0] if len(df_metadata) > 0 else None
            
            # If not found in columns, check if it's in a key-value format
            if period_start is None or period_end is None:
                # Check for key-value pairs in rows
                for idx, row in df_metadata.iterrows():
                    for col in df_metadata.columns:
                        cell_value = str(row[col]).lower() if pd.notna(row[col]) else ''
                        if 'period_start' in cell_value or 'period start' in cell_value:
                            # Get the next column value
                            cols = list(df_metadata.columns)
                            col_idx = cols.index(col)
                            if col_idx + 1 < len(cols):
                                period_start = row[cols[col_idx + 1]]
                        if 'period_end' in cell_value or 'period end' in cell_value:
                            cols = list(df_metadata.columns)
                            col_idx = cols.index(col)
                            if col_idx + 1 < len(cols):
                                period_end = row[cols[col_idx + 1]]
            
            print(f"[INFO] Extracted period_start: {period_start}")
            print(f"[INFO] Extracted period_end: {period_end}")
            
            # Add the period columns to ledger_master
            df_ledger['period_start'] = period_start
            df_ledger['period_end'] = period_end
            
            df = df_ledger
            print(f"[INFO] Added period_start and period_end columns to ledger data")
        
        # Save to Excel
        print(f"[INFO] Saving result to Excel: {output_xlsx}")
        df.to_excel(output_xlsx, index=False)
        print(f"[SUCCESS] Excel file saved: {output_xlsx}")
        
        # Save to JSON
        print(f"[INFO] Saving result to JSON: {output_json}")
        df.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"[SUCCESS] JSON file saved: {output_json}")
        
        # Print summary
        print(f"\n[SUMMARY]")
        print(f"  - Total rows: {len(df)}")
        print(f"  - Total columns: {len(df.columns)}")
        print(f"  - Columns: {list(df.columns)}")
        print(f"\n[INFO] Transformation complete!")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()