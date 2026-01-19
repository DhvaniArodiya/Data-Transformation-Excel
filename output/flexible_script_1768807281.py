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
        
        # Load the ledger_master sheet
        if 'ledger_master' in xl.sheet_names:
            ledger_df = pd.read_excel(input_path, sheet_name='ledger_master')
            print(f"[INFO] Loaded 'ledger_master' sheet with {len(ledger_df)} rows and {len(ledger_df.columns)} columns")
        else:
            # Try to find a sheet that might contain ledger data or use the first sheet
            print(f"[WARNING] 'ledger_master' sheet not found. Checking available sheets...")
            ledger_df = pd.read_excel(input_path, sheet_name=0)
            print(f"[INFO] Loaded first sheet with {len(ledger_df)} rows and {len(ledger_df.columns)} columns")
        
        print(f"[INFO] Ledger columns: {ledger_df.columns.tolist()}")
        
        # Load the report_metadata sheet to extract period dates
        period_start = None
        period_end = None
        
        if 'report_metadata' in xl.sheet_names:
            metadata_df = pd.read_excel(input_path, sheet_name='report_metadata')
            print(f"[INFO] Loaded 'report_metadata' sheet with {len(metadata_df)} rows and {len(metadata_df.columns)} columns")
            print(f"[INFO] Metadata columns: {metadata_df.columns.tolist()}")
            print(f"[INFO] Metadata content:\n{metadata_df}")
            
            # Try to extract period start and end dates
            # Common patterns: look for columns or rows containing 'start', 'end', 'period', 'date'
            
            # Check if there are columns with these names
            cols_lower = [str(c).lower() for c in metadata_df.columns]
            
            # Try column-based extraction
            for i, col in enumerate(metadata_df.columns):
                col_lower = str(col).lower()
                if 'start' in col_lower or 'period_start' in col_lower:
                    period_start = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                    print(f"[INFO] Found period_start in column '{col}': {period_start}")
                if 'end' in col_lower or 'period_end' in col_lower:
                    period_end = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                    print(f"[INFO] Found period_end in column '{col}': {period_end}")
            
            # If not found in columns, try row-based extraction (key-value format)
            if period_start is None or period_end is None:
                # Check if metadata is in key-value format (first column = key, second column = value)
                if len(metadata_df.columns) >= 2:
                    for idx, row in metadata_df.iterrows():
                        key = str(row.iloc[0]).lower() if pd.notna(row.iloc[0]) else ''
                        value = row.iloc[1] if len(row) > 1 else None
                        
                        if 'start' in key and period_start is None:
                            period_start = value
                            print(f"[INFO] Found period_start from row key '{row.iloc[0]}': {period_start}")
                        if 'end' in key and period_end is None:
                            period_end = value
                            print(f"[INFO] Found period_end from row key '{row.iloc[0]}': {period_end}")
                
                # Also check if the first row contains headers that might indicate dates
                if period_start is None or period_end is None:
                    for col in metadata_df.columns:
                        col_str = str(col).lower()
                        if ('report' in col_str or 'period' in col_str or 'date' in col_str):
                            # Check the values in this column
                            for idx, val in enumerate(metadata_df[col]):
                                val_str = str(val).lower() if pd.notna(val) else ''
                                if 'start' in val_str and period_start is None:
                                    # The date might be in the next column
                                    col_idx = metadata_df.columns.get_loc(col)
                                    if col_idx + 1 < len(metadata_df.columns):
                                        period_start = metadata_df.iloc[idx, col_idx + 1]
                                        print(f"[INFO] Found period_start: {period_start}")
                                if 'end' in val_str and period_end is None:
                                    col_idx = metadata_df.columns.get_loc(col)
                                    if col_idx + 1 < len(metadata_df.columns):
                                        period_end = metadata_df.iloc[idx, col_idx + 1]
                                        print(f"[INFO] Found period_end: {period_end}")
        else:
            print(f"[WARNING] 'report_metadata' sheet not found in the Excel file")
            print(f"[INFO] Will add empty period_start and period_end columns")
        
        # Add the period columns to the ledger dataframe
        ledger_df['period_start'] = period_start
        ledger_df['period_end'] = period_end
        
        print(f"[INFO] Added 'period_start' column with value: {period_start}")
        print(f"[INFO] Added 'period_end' column with value: {period_end}")
        print(f"[INFO] Final columns: {ledger_df.columns.tolist()}")
        print(f"[INFO] Final dataframe shape: {ledger_df.shape}")
        
        # Display sample of the result
        print(f"\n[INFO] Sample of transformed data:")
        print(ledger_df.head())
        
        # Save to Excel
        ledger_df.to_excel(output_xlsx, index=False)
        print(f"\n[SUCCESS] Saved Excel output to: {output_xlsx}")
        
        # Save to JSON
        # Convert datetime objects to string for JSON serialization
        ledger_json = ledger_df.copy()
        for col in ledger_json.columns:
            if ledger_json[col].dtype == 'datetime64[ns]':
                ledger_json[col] = ledger_json[col].astype(str)
        
        ledger_json.to_json(output_json, orient='records', indent=2, date_format='iso')
        print(f"[SUCCESS] Saved JSON output to: {output_json}")
        
        print(f"\n[COMPLETE] Transformation finished successfully!")
        print(f"[INFO] Total rows processed: {len(ledger_df)}")
        print(f"[INFO] Total columns in output: {len(ledger_df.columns)}")
        
    except FileNotFoundError:
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()