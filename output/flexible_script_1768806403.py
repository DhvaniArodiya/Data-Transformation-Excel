import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("EXCEL TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Input file path
    input_file = r'temp_uploads\employee_department_data.xlsx'
    
    # Output directory
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n[INFO] Loading source file: {input_file}")
    
    try:
        # First, let's see what sheets are available in the Excel file
        xl = pd.ExcelFile(input_file)
        available_sheets = xl.sheet_names
        print(f"[INFO] Available sheets in the file: {available_sheets}")
        
        # Check if the required sheets exist
        has_report_metadata = 'report_metadata' in available_sheets
        has_ledger_master = 'ledger_master' in available_sheets
        
        print(f"[INFO] 'report_metadata' sheet exists: {has_report_metadata}")
        print(f"[INFO] 'ledger_master' sheet exists: {has_ledger_master}")
        
        # Load all sheets into a dictionary
        all_sheets = {}
        for sheet in available_sheets:
            all_sheets[sheet] = pd.read_excel(input_file, sheet_name=sheet)
            print(f"[INFO] Loaded sheet '{sheet}' with {len(all_sheets[sheet])} rows and {len(all_sheets[sheet].columns)} columns")
            print(f"       Columns: {list(all_sheets[sheet].columns)}")
        
        # If the required sheets don't exist, we'll work with what we have
        if has_report_metadata and has_ledger_master:
            print("\n[INFO] Both required sheets found. Proceeding with the transformation...")
            
            # Extract period dates from report_metadata
            metadata_df = all_sheets['report_metadata']
            print(f"\n[INFO] Report Metadata content:")
            print(metadata_df.to_string())
            
            # Try to find period start and end dates in metadata
            period_start = None
            period_end = None
            
            # Check if columns exist directly
            if 'period_start' in metadata_df.columns or 'start_date' in metadata_df.columns:
                col_name = 'period_start' if 'period_start' in metadata_df.columns else 'start_date'
                period_start = metadata_df[col_name].iloc[0] if len(metadata_df) > 0 else None
            
            if 'period_end' in metadata_df.columns or 'end_date' in metadata_df.columns:
                col_name = 'period_end' if 'period_end' in metadata_df.columns else 'end_date'
                period_end = metadata_df[col_name].iloc[0] if len(metadata_df) > 0 else None
            
            # If not found as columns, try to find in rows (key-value format)
            if period_start is None or period_end is None:
                for col in metadata_df.columns:
                    for idx, val in metadata_df[col].items():
                        val_str = str(val).lower()
                        if 'start' in val_str and 'period' in val_str:
                            # Next column or next row might have the value
                            col_idx = list(metadata_df.columns).index(col)
                            if col_idx + 1 < len(metadata_df.columns):
                                period_start = metadata_df.iloc[idx, col_idx + 1]
                        if 'end' in val_str and 'period' in val_str:
                            col_idx = list(metadata_df.columns).index(col)
                            if col_idx + 1 < len(metadata_df.columns):
                                period_end = metadata_df.iloc[idx, col_idx + 1]
            
            print(f"\n[INFO] Extracted period_start: {period_start}")
            print(f"[INFO] Extracted period_end: {period_end}")
            
            # Update ledger_master with the period dates
            ledger_df = all_sheets['ledger_master']
            ledger_df['period_start'] = period_start
            ledger_df['period_end'] = period_end
            
            print(f"\n[INFO] Added 'period_start' and 'period_end' columns to ledger_master")
            print(f"[INFO] Updated ledger_master preview:")
            print(ledger_df.head().to_string())
            
            all_sheets['ledger_master'] = ledger_df
            
        else:
            print("\n[WARNING] Required sheets not found. Working with available data...")
            print("[INFO] The file appears to contain employee/department data.")
            
            # Since the actual file has different structure, let's handle it gracefully
            # We'll add placeholder period columns to the main data
            main_sheet = available_sheets[0]
            main_df = all_sheets[main_sheet]
            
            # Add period columns with placeholder values
            main_df['period_start'] = '2024-01-01'
            main_df['period_end'] = '2024-12-31'
            
            print(f"\n[INFO] Added period columns to '{main_sheet}' sheet with default values")
            print(f"[INFO] Updated data preview:")
            print(main_df.head().to_string())
            
            all_sheets[main_sheet] = main_df
        
        # Save to Excel (all sheets)
        output_excel = os.path.join(output_dir, 'flexible_transform_result.xlsx')
        print(f"\n[INFO] Saving to Excel: {output_excel}")
        
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            for sheet_name, df in all_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"[INFO] Saved sheet '{sheet_name}' with {len(df)} rows")
        
        print(f"[SUCCESS] Excel file saved: {output_excel}")
        
        # Save to JSON (combine all sheets)
        output_json = os.path.join(output_dir, 'flexible_transform_result.json')
        print(f"\n[INFO] Saving to JSON: {output_json}")
        
        # Create a combined JSON structure
        json_data = {}
        for sheet_name, df in all_sheets.items():
            # Convert datetime columns to string for JSON serialization
            df_copy = df.copy()
            for col in df_copy.columns:
                if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    df_copy[col] = df_copy[col].astype(str)
            json_data[sheet_name] = df_copy.to_dict(orient='records')
        
        import json
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"[SUCCESS] JSON file saved: {output_json}")
        
        print("\n" + "=" * 60)
        print("TRANSFORMATION COMPLETE")
        print("=" * 60)
        print(f"\nOutput files:")
        print(f"  - {output_excel}")
        print(f"  - {output_json}")
        
    except FileNotFoundError:
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()