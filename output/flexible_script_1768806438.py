import pandas as pd
import os
import sys

def main():
    # Input and output paths
    input_path = 'temp_uploads/age_sample.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading Excel file: {input_path}")
    
    # First, let's check what sheets are available in the Excel file
    xl = pd.ExcelFile(input_path)
    available_sheets = xl.sheet_names
    print(f"Available sheets in the file: {available_sheets}")
    
    # Check if the required sheets exist
    has_report_metadata = 'report_metadata' in available_sheets
    has_ledger_master = 'ledger_master' in available_sheets
    
    print(f"'report_metadata' sheet exists: {has_report_metadata}")
    print(f"'ledger_master' sheet exists: {has_ledger_master}")
    
    # Load all sheets into a dictionary
    all_sheets = {}
    for sheet in available_sheets:
        all_sheets[sheet] = pd.read_excel(input_path, sheet_name=sheet)
        print(f"Loaded sheet '{sheet}' with {len(all_sheets[sheet])} rows and columns: {list(all_sheets[sheet].columns)}")
    
    # If the required sheets don't exist, we'll work with what we have
    if has_report_metadata and has_ledger_master:
        # Extract period start and end from report_metadata
        metadata_df = all_sheets['report_metadata']
        print(f"\nReport metadata columns: {list(metadata_df.columns)}")
        print(f"Report metadata content:\n{metadata_df}")
        
        # Try to find period start and end dates in metadata
        period_start = None
        period_end = None
        
        # Common column name patterns for period dates
        start_patterns = ['period_start', 'start_date', 'reporting_period_start', 'from_date', 'begin_date']
        end_patterns = ['period_end', 'end_date', 'reporting_period_end', 'to_date', 'finish_date']
        
        # Check columns for start date
        for col in metadata_df.columns:
            col_lower = col.lower().replace(' ', '_')
            if any(pattern in col_lower for pattern in start_patterns):
                period_start = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                print(f"Found period start in column '{col}': {period_start}")
                break
        
        # Check columns for end date
        for col in metadata_df.columns:
            col_lower = col.lower().replace(' ', '_')
            if any(pattern in col_lower for pattern in end_patterns):
                period_end = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                print(f"Found period end in column '{col}': {period_end}")
                break
        
        # If not found in columns, check if metadata is in key-value format
        if period_start is None or period_end is None:
            # Check for key-value structure
            for col in metadata_df.columns:
                if metadata_df[col].dtype == 'object':
                    for idx, val in metadata_df[col].items():
                        if isinstance(val, str):
                            val_lower = val.lower().replace(' ', '_')
                            if any(pattern in val_lower for pattern in start_patterns) and period_start is None:
                                # Get the value from the next column
                                col_idx = list(metadata_df.columns).index(col)
                                if col_idx + 1 < len(metadata_df.columns):
                                    period_start = metadata_df.iloc[idx, col_idx + 1]
                                    print(f"Found period start (key-value): {period_start}")
                            elif any(pattern in val_lower for pattern in end_patterns) and period_end is None:
                                col_idx = list(metadata_df.columns).index(col)
                                if col_idx + 1 < len(metadata_df.columns):
                                    period_end = metadata_df.iloc[idx, col_idx + 1]
                                    print(f"Found period end (key-value): {period_end}")
        
        # Add the period columns to ledger_master
        ledger_df = all_sheets['ledger_master']
        ledger_df['period_start'] = period_start
        ledger_df['period_end'] = period_end
        all_sheets['ledger_master'] = ledger_df
        
        print(f"\nAdded 'period_start' ({period_start}) and 'period_end' ({period_end}) to ledger_master")
        print(f"Updated ledger_master columns: {list(ledger_df.columns)}")
        
    else:
        # The required sheets don't exist - work with the main data
        print("\nRequired sheets 'report_metadata' and/or 'ledger_master' not found.")
        print("Working with available data and adding placeholder period columns.")
        
        # Get the main data (first sheet or the one with data)
        main_sheet_name = available_sheets[0]
        main_df = all_sheets[main_sheet_name]
        
        # Add placeholder period columns
        main_df['period_start'] = pd.NaT  # Not a Time - placeholder for dates
        main_df['period_end'] = pd.NaT
        
        all_sheets[main_sheet_name] = main_df
        print(f"Added placeholder 'period_start' and 'period_end' columns to '{main_sheet_name}'")
    
    # Save to Excel with all sheets
    print(f"\nSaving to Excel: {output_xlsx}")
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        for sheet_name, df in all_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  - Saved sheet '{sheet_name}' with {len(df)} rows")
    
    # Save to JSON (combine all sheets into a single JSON structure)
    print(f"Saving to JSON: {output_json}")
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
    
    print("\n" + "="*50)
    print("TRANSFORMATION COMPLETE")
    print("="*50)
    print(f"Excel output: {output_xlsx}")
    print(f"JSON output: {output_json}")

if __name__ == "__main__":
    main()