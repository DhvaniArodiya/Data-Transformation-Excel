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
        
        # Read the report_metadata sheet to get period start and end values
        print("[INFO] Reading 'report_metadata' sheet...")
        
        if 'report_metadata' in xl.sheet_names:
            metadata_df = pd.read_excel(input_path, sheet_name='report_metadata')
            print(f"[INFO] report_metadata shape: {metadata_df.shape}")
            print(f"[INFO] report_metadata columns: {metadata_df.columns.tolist()}")
            print(f"[INFO] report_metadata content:\n{metadata_df}")
            
            # Extract period_start and period_end values
            # Common patterns: could be in rows or columns
            period_start = None
            period_end = None
            
            # Try to find period_start and period_end in the metadata
            # Check if they are column names
            if 'period_start' in metadata_df.columns:
                period_start = metadata_df['period_start'].iloc[0]
            if 'period_end' in metadata_df.columns:
                period_end = metadata_df['period_end'].iloc[0]
            
            # If not found as columns, check if they are row labels (first column as keys)
            if period_start is None or period_end is None:
                # Check if first column contains labels like 'period_start', 'period_end'
                first_col = metadata_df.columns[0]
                for idx, row in metadata_df.iterrows():
                    key = str(row[first_col]).lower().strip() if pd.notna(row[first_col]) else ''
                    if 'period_start' in key or 'period start' in key:
                        # Value is likely in the second column
                        if len(metadata_df.columns) > 1:
                            period_start = row[metadata_df.columns[1]]
                    if 'period_end' in key or 'period end' in key:
                        if len(metadata_df.columns) > 1:
                            period_end = row[metadata_df.columns[1]]
            
            print(f"[INFO] Extracted period_start: {period_start}")
            print(f"[INFO] Extracted period_end: {period_end}")
        else:
            print("[WARNING] 'report_metadata' sheet not found. Looking for alternative names...")
            # Try case-insensitive match
            for sheet in xl.sheet_names:
                if 'metadata' in sheet.lower() or 'report' in sheet.lower():
                    metadata_df = pd.read_excel(input_path, sheet_name=sheet)
                    print(f"[INFO] Found alternative metadata sheet: {sheet}")
                    print(f"[INFO] Content:\n{metadata_df}")
                    break
            period_start = None
            period_end = None
        
        # Read the ledger_master sheet
        print("[INFO] Reading 'ledger_master' sheet...")
        
        if 'ledger_master' in xl.sheet_names:
            ledger_df = pd.read_excel(input_path, sheet_name='ledger_master')
        else:
            # Try to find it or use the first sheet
            ledger_sheet = None
            for sheet in xl.sheet_names:
                if 'ledger' in sheet.lower():
                    ledger_sheet = sheet
                    break
            if ledger_sheet is None:
                # Use first sheet that's not metadata
                for sheet in xl.sheet_names:
                    if 'metadata' not in sheet.lower():
                        ledger_sheet = sheet
                        break
            if ledger_sheet is None:
                ledger_sheet = xl.sheet_names[0]
            
            print(f"[INFO] Using sheet '{ledger_sheet}' as ledger_master")
            ledger_df = pd.read_excel(input_path, sheet_name=ledger_sheet)
        
        print(f"[INFO] ledger_master shape: {ledger_df.shape}")
        print(f"[INFO] ledger_master columns: {ledger_df.columns.tolist()}")
        print(f"[INFO] Original ledger_master data:\n{ledger_df}")
        
        # Add the new columns
        print("[INFO] Adding 'period_start' and 'period_end' columns to ledger_master...")
        ledger_df['period_start'] = period_start
        ledger_df['period_end'] = period_end
        
        print(f"[INFO] Updated ledger_master data:\n{ledger_df}")
        
        # Save to Excel
        print(f"[INFO] Saving result to: {output_xlsx}")
        ledger_df.to_excel(output_xlsx, index=False)
        print(f"[SUCCESS] Excel file saved: {output_xlsx}")
        
        # Save to JSON
        print(f"[INFO] Saving result to: {output_json}")
        # Convert datetime objects to string for JSON serialization
        ledger_df_json = ledger_df.copy()
        for col in ledger_df_json.columns:
            if pd.api.types.is_datetime64_any_dtype(ledger_df_json[col]):
                ledger_df_json[col] = ledger_df_json[col].astype(str)
        
        ledger_df_json.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"[SUCCESS] JSON file saved: {output_json}")
        
        print("\n[COMPLETE] Transformation completed successfully!")
        print(f"[INFO] Final output has {len(ledger_df)} rows and {len(ledger_df.columns)} columns")
        print(f"[INFO] Columns: {ledger_df.columns.tolist()}")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()