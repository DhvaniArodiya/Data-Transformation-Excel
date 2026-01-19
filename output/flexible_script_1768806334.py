import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = 'temp_uploads/Sample_data.xlsx'
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
        print(f"[INFO] Available sheets: {xl.sheet_names}")
        
        # Load the report_metadata sheet
        print("[INFO] Loading 'report_metadata' sheet...")
        try:
            report_metadata = pd.read_excel(input_path, sheet_name='report_metadata')
            print(f"[INFO] report_metadata shape: {report_metadata.shape}")
            print(f"[INFO] report_metadata columns: {list(report_metadata.columns)}")
            print(f"[INFO] report_metadata content:\n{report_metadata}")
        except Exception as e:
            print(f"[ERROR] Could not load 'report_metadata' sheet: {e}")
            # Try alternative sheet names
            for sheet in xl.sheet_names:
                if 'metadata' in sheet.lower() or 'report' in sheet.lower():
                    print(f"[INFO] Trying alternative sheet: {sheet}")
                    report_metadata = pd.read_excel(input_path, sheet_name=sheet)
                    break
            else:
                raise ValueError("Could not find report_metadata sheet")
        
        # Load the ledger_master sheet
        print("[INFO] Loading 'ledger_master' sheet...")
        try:
            ledger_master = pd.read_excel(input_path, sheet_name='ledger_master')
            print(f"[INFO] ledger_master shape: {ledger_master.shape}")
            print(f"[INFO] ledger_master columns: {list(ledger_master.columns)}")
        except Exception as e:
            print(f"[ERROR] Could not load 'ledger_master' sheet: {e}")
            # Try the first sheet or alternative names
            for sheet in xl.sheet_names:
                if 'ledger' in sheet.lower() or 'master' in sheet.lower():
                    print(f"[INFO] Trying alternative sheet: {sheet}")
                    ledger_master = pd.read_excel(input_path, sheet_name=sheet)
                    break
            else:
                # Default to first sheet
                print(f"[INFO] Using first sheet: {xl.sheet_names[0]}")
                ledger_master = pd.read_excel(input_path, sheet_name=xl.sheet_names[0])
        
        # Extract period_start and period_end from report_metadata
        print("[INFO] Extracting period_start and period_end values from report_metadata...")
        
        # The metadata might be in different formats - let's handle common cases
        period_start = None
        period_end = None
        
        # Check if it's a key-value format (column with field names and column with values)
        if report_metadata.shape[1] >= 2:
            # Try to find period_start and period_end in the data
            for idx, row in report_metadata.iterrows():
                row_values = [str(v).lower().strip() for v in row.values if pd.notna(v)]
                for i, val in enumerate(row.values):
                    if pd.notna(val) and 'period' in str(val).lower() and 'start' in str(val).lower():
                        # The value should be in the next column or same row
                        if i + 1 < len(row.values) and pd.notna(row.values[i + 1]):
                            period_start = row.values[i + 1]
                    if pd.notna(val) and 'period' in str(val).lower() and 'end' in str(val).lower():
                        if i + 1 < len(row.values) and pd.notna(row.values[i + 1]):
                            period_end = row.values[i + 1]
        
        # Alternative: Check if columns are named period_start, period_end
        if period_start is None and 'period_start' in report_metadata.columns:
            period_start = report_metadata['period_start'].iloc[0]
        if period_end is None and 'period_end' in report_metadata.columns:
            period_end = report_metadata['period_end'].iloc[0]
        
        # Another alternative: Check for variations in column names
        for col in report_metadata.columns:
            col_lower = str(col).lower()
            if period_start is None and 'period' in col_lower and 'start' in col_lower:
                period_start = report_metadata[col].iloc[0]
            if period_end is None and 'period' in col_lower and 'end' in col_lower:
                period_end = report_metadata[col].iloc[0]
        
        # If still not found, try treating first column as keys
        if period_start is None or period_end is None:
            first_col = report_metadata.columns[0]
            if report_metadata.shape[1] >= 2:
                second_col = report_metadata.columns[1]
                for idx, row in report_metadata.iterrows():
                    key = str(row[first_col]).lower().strip() if pd.notna(row[first_col]) else ''
                    if 'period_start' in key or 'period start' in key:
                        period_start = row[second_col]
                    if 'period_end' in key or 'period end' in key:
                        period_end = row[second_col]
        
        print(f"[INFO] Extracted period_start: {period_start}")
        print(f"[INFO] Extracted period_end: {period_end}")
        
        if period_start is None:
            print("[WARNING] Could not find period_start value, setting to None")
        if period_end is None:
            print("[WARNING] Could not find period_end value, setting to None")
        
        # Add the new columns to ledger_master
        print("[INFO] Adding period_start and period_end columns to ledger_master...")
        ledger_master['period_start'] = period_start
        ledger_master['period_end'] = period_end
        
        print(f"[INFO] Updated ledger_master columns: {list(ledger_master.columns)}")
        print(f"[INFO] Updated ledger_master shape: {ledger_master.shape}")
        print(f"[INFO] Sample of updated data:\n{ledger_master.head()}")
        
        # Save to Excel
        print(f"[INFO] Saving result to Excel: {output_xlsx}")
        ledger_master.to_excel(output_xlsx, index=False)
        print(f"[SUCCESS] Excel file saved: {output_xlsx}")
        
        # Save to JSON
        print(f"[INFO] Saving result to JSON: {output_json}")
        # Convert datetime objects to string for JSON serialization
        ledger_master_json = ledger_master.copy()
        for col in ledger_master_json.columns:
            if ledger_master_json[col].dtype == 'datetime64[ns]':
                ledger_master_json[col] = ledger_master_json[col].astype(str)
        ledger_master_json.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"[SUCCESS] JSON file saved: {output_json}")
        
        print("[INFO] Transformation completed successfully!")
        print(f"[INFO] Final output has {len(ledger_master)} rows and {len(ledger_master.columns)} columns")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()