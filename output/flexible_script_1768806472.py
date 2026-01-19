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
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory ensured: {output_dir}")
    
    # Load the Excel file
    print(f"[INFO] Loading Excel file: {input_path}")
    
    try:
        # First, let's see what sheets are available
        xl = pd.ExcelFile(input_path)
        print(f"[INFO] Available sheets: {xl.sheet_names}")
        
        # Load the ledger_master sheet (or the main data sheet)
        # Try different possible sheet names
        ledger_sheet_name = None
        metadata_sheet_name = None
        
        for sheet in xl.sheet_names:
            sheet_lower = sheet.lower()
            if 'ledger' in sheet_lower or 'master' in sheet_lower:
                ledger_sheet_name = sheet
            if 'metadata' in sheet_lower or 'report' in sheet_lower:
                metadata_sheet_name = sheet
        
        # If no specific sheets found, use first sheet as ledger and look for metadata
        if ledger_sheet_name is None:
            ledger_sheet_name = xl.sheet_names[0]
            print(f"[INFO] No 'ledger_master' sheet found, using first sheet: {ledger_sheet_name}")
        else:
            print(f"[INFO] Found ledger sheet: {ledger_sheet_name}")
        
        # Load ledger data
        df_ledger = pd.read_excel(input_path, sheet_name=ledger_sheet_name)
        print(f"[INFO] Loaded ledger data with {len(df_ledger)} rows and columns: {list(df_ledger.columns)}")
        
        # Try to load metadata sheet
        period_start = None
        period_end = None
        
        if metadata_sheet_name:
            print(f"[INFO] Found metadata sheet: {metadata_sheet_name}")
            df_metadata = pd.read_excel(input_path, sheet_name=metadata_sheet_name)
            print(f"[INFO] Metadata sheet columns: {list(df_metadata.columns)}")
            print(f"[INFO] Metadata content:\n{df_metadata}")
            
            # Try to extract period start and end dates from metadata
            # Common patterns: look for rows/columns with 'start', 'end', 'period', 'date'
            for col in df_metadata.columns:
                col_lower = str(col).lower()
                if 'start' in col_lower or 'begin' in col_lower:
                    period_start = df_metadata[col].iloc[0] if len(df_metadata) > 0 else None
                if 'end' in col_lower:
                    period_end = df_metadata[col].iloc[0] if len(df_metadata) > 0 else None
            
            # If not found in columns, check row values
            if period_start is None or period_end is None:
                for idx, row in df_metadata.iterrows():
                    for col in df_metadata.columns:
                        cell_val = str(row[col]).lower() if pd.notna(row[col]) else ''
                        if 'start' in cell_val or 'begin' in cell_val:
                            # Get the next column value or next row
                            col_idx = df_metadata.columns.get_loc(col)
                            if col_idx + 1 < len(df_metadata.columns):
                                period_start = row[df_metadata.columns[col_idx + 1]]
                        if 'end' in cell_val:
                            col_idx = df_metadata.columns.get_loc(col)
                            if col_idx + 1 < len(df_metadata.columns):
                                period_end = row[df_metadata.columns[col_idx + 1]]
        else:
            # Check if there are multiple sheets and try to find metadata
            print(f"[INFO] No dedicated metadata sheet found. Checking all sheets...")
            for sheet in xl.sheet_names:
                if sheet != ledger_sheet_name:
                    df_temp = pd.read_excel(input_path, sheet_name=sheet)
                    print(f"[INFO] Checking sheet '{sheet}': {list(df_temp.columns)}")
                    
                    # Look for period information
                    for col in df_temp.columns:
                        col_lower = str(col).lower()
                        if 'start' in col_lower and 'period' in col_lower:
                            period_start = df_temp[col].iloc[0] if len(df_temp) > 0 else None
                        if 'end' in col_lower and 'period' in col_lower:
                            period_end = df_temp[col].iloc[0] if len(df_temp) > 0 else None
        
        # If still not found, set default values or extract from any available date columns
        if period_start is None:
            print("[WARNING] Could not find period_start in metadata. Setting default value.")
            period_start = "2024-01-01"
        
        if period_end is None:
            print("[WARNING] Could not find period_end in metadata. Setting default value.")
            period_end = "2024-12-31"
        
        print(f"[INFO] Period Start: {period_start}")
        print(f"[INFO] Period End: {period_end}")
        
        # Add the period columns to the ledger data
        df_ledger['period_start'] = period_start
        df_ledger['period_end'] = period_end
        
        print(f"[INFO] Added 'period_start' and 'period_end' columns to ledger data")
        print(f"[INFO] Updated columns: {list(df_ledger.columns)}")
        
        # Display sample of the result
        print(f"\n[INFO] Sample of transformed data:")
        print(df_ledger.head())
        
        # Save to Excel
        df_ledger.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"\n[SUCCESS] Saved Excel output to: {output_xlsx}")
        
        # Save to JSON
        # Convert datetime objects to string for JSON serialization
        df_json = df_ledger.copy()
        for col in df_json.columns:
            if df_json[col].dtype == 'datetime64[ns]':
                df_json[col] = df_json[col].astype(str)
        
        df_json.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"[SUCCESS] Saved JSON output to: {output_json}")
        
        print(f"\n[COMPLETE] Transformation finished successfully!")
        print(f"[INFO] Total records processed: {len(df_ledger)}")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()