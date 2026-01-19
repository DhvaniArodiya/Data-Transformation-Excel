import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("STARTING TRANSFORMATION SCRIPT")
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
    
    # First, let's see what sheets are available in the Excel file
    try:
        xl = pd.ExcelFile(input_path)
        sheet_names = xl.sheet_names
        print(f"Available sheets in the Excel file: {sheet_names}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)
    
    # Load all sheets to understand the structure
    all_sheets = {}
    for sheet in sheet_names:
        all_sheets[sheet] = pd.read_excel(input_path, sheet_name=sheet)
        print(f"\nSheet '{sheet}' - Shape: {all_sheets[sheet].shape}")
        print(f"Columns: {list(all_sheets[sheet].columns)}")
        print(f"First few rows:\n{all_sheets[sheet].head()}")
    
    # Look for report_metadata sheet (case-insensitive search)
    report_metadata_sheet = None
    ledger_master_sheet = None
    
    for sheet in sheet_names:
        if 'report_metadata' in sheet.lower() or 'metadata' in sheet.lower():
            report_metadata_sheet = sheet
        if 'ledger_master' in sheet.lower() or 'ledger' in sheet.lower():
            ledger_master_sheet = sheet
    
    # If specific sheets not found, try to work with available data
    if report_metadata_sheet is None or ledger_master_sheet is None:
        print("\n" + "=" * 60)
        print("NOTE: Specific sheets 'report_metadata' and 'ledger_master' not found.")
        print("Working with available data structure...")
        print("=" * 60)
        
        # If there's only one sheet or we need to handle differently
        if len(sheet_names) == 1:
            # Single sheet scenario - just copy the data
            df = all_sheets[sheet_names[0]]
            print(f"\nUsing single sheet: {sheet_names[0]}")
            
            # Add placeholder period columns if they don't exist
            if 'period_start' not in df.columns:
                df['period_start'] = None
                print("Added 'period_start' column (no metadata source found)")
            if 'period_end' not in df.columns:
                df['period_end'] = None
                print("Added 'period_end' column (no metadata source found)")
        else:
            # Multiple sheets - try to find metadata-like and data-like sheets
            # Assume first sheet might be data, look for metadata in others
            df = all_sheets[sheet_names[0]].copy()
            
            # Search for period information in other sheets
            period_start = None
            period_end = None
            
            for sheet in sheet_names[1:]:
                metadata_df = all_sheets[sheet]
                # Look for period-related columns or values
                for col in metadata_df.columns:
                    col_lower = str(col).lower()
                    if 'period' in col_lower and 'start' in col_lower:
                        period_start = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                    elif 'period' in col_lower and 'end' in col_lower:
                        period_end = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                    elif 'start' in col_lower:
                        period_start = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                    elif 'end' in col_lower:
                        period_end = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
                
                # Also check row values for key-value pairs
                for idx, row in metadata_df.iterrows():
                    for val in row.values:
                        val_str = str(val).lower()
                        if 'period_start' in val_str or 'period start' in val_str:
                            # Next value might be the actual date
                            vals = list(row.values)
                            val_idx = [str(v).lower() for v in vals].index(val_str)
                            if val_idx + 1 < len(vals):
                                period_start = vals[val_idx + 1]
                        elif 'period_end' in val_str or 'period end' in val_str:
                            vals = list(row.values)
                            val_idx = [str(v).lower() for v in vals].index(val_str)
                            if val_idx + 1 < len(vals):
                                period_end = vals[val_idx + 1]
            
            df['period_start'] = period_start
            df['period_end'] = period_end
            print(f"\nAdded period_start: {period_start}")
            print(f"Added period_end: {period_end}")
    else:
        # Found both sheets
        print(f"\nFound report_metadata sheet: {report_metadata_sheet}")
        print(f"Found ledger_master sheet: {ledger_master_sheet}")
        
        metadata_df = all_sheets[report_metadata_sheet]
        df = all_sheets[ledger_master_sheet].copy()
        
        # Extract period_start and period_end from metadata
        period_start = None
        period_end = None
        
        # Try different approaches to find the values
        # Approach 1: Look for columns named period_start/period_end
        for col in metadata_df.columns:
            col_lower = str(col).lower().replace(' ', '_')
            if 'period_start' in col_lower:
                period_start = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
            elif 'period_end' in col_lower:
                period_end = metadata_df[col].iloc[0] if len(metadata_df) > 0 else None
        
        # Approach 2: Look for key-value structure
        if period_start is None or period_end is None:
            for idx, row in metadata_df.iterrows():
                for i, val in enumerate(row.values):
                    val_str = str(val).lower().replace(' ', '_')
                    if 'period_start' in val_str:
                        if i + 1 < len(row.values):
                            period_start = row.values[i + 1]
                    elif 'period_end' in val_str:
                        if i + 1 < len(row.values):
                            period_end = row.values[i + 1]
        
        df['period_start'] = period_start
        df['period_end'] = period_end
        print(f"\nExtracted period_start: {period_start}")
        print(f"Extracted period_end: {period_end}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"\nFinal DataFrame shape: {df.shape}")
    print(f"Final columns: {list(df.columns)}")
    print(f"\nFirst few rows of transformed data:\n{df.head()}")
    
    # Save to Excel
    print(f"\nSaving to Excel: {output_xlsx}")
    df.to_excel(output_xlsx, index=False)
    print("Excel file saved successfully!")
    
    # Save to JSON
    print(f"Saving to JSON: {output_json}")
    # Convert datetime columns to string for JSON serialization
    df_json = df.copy()
    for col in df_json.columns:
        if df_json[col].dtype == 'datetime64[ns]':
            df_json[col] = df_json[col].astype(str)
    df_json.to_json(output_json, orient='records', indent=2, date_format='iso')
    print("JSON file saved successfully!")
    
    print("\n" + "=" * 60)
    print("SCRIPT COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    main()