import pandas as pd
import os
import sys

def main():
    source_path = 'temp_uploads/Sample_data.xlsx'
    output_dir = 'output'
    output_excel = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading source file: {source_path}")
    
    # 1. Load ALL sheets from the Excel file
    all_sheets = pd.read_excel(source_path, sheet_name=None)
    
    print(f"Found {len(all_sheets)} sheet(s): {list(all_sheets.keys())}")
    
    # 2. Read period_start and period_end from "report_metadata" sheet
    if 'report_metadata' not in all_sheets:
        print("ERROR: 'report_metadata' sheet not found in the Excel file.")
        print(f"Available sheets: {list(all_sheets.keys())}")
        sys.exit(1)
    
    metadata_df = all_sheets['report_metadata']
    print(f"\nReport Metadata sheet contents:")
    print(metadata_df)
    
    # Try to extract period_start and period_end values
    # Common patterns: values might be in rows with labels, or in specific columns
    period_start = None
    period_end = None
    
    # Check if metadata has columns that might contain the values
    metadata_cols = metadata_df.columns.tolist()
    print(f"\nMetadata columns: {metadata_cols}")
    
    # Pattern 1: Look for rows where first column contains 'period_start' or 'period_end'
    for idx, row in metadata_df.iterrows():
        row_values = [str(v).lower().strip() for v in row.values if pd.notna(v)]
        for i, val in enumerate(row.values):
            if pd.notna(val):
                val_str = str(val).lower().strip()
                if 'period_start' in val_str or 'period start' in val_str:
                    # Get the next non-null value in the row
                    for j in range(i+1, len(row.values)):
                        if pd.notna(row.values[j]):
                            period_start = row.values[j]
                            break
                elif 'period_end' in val_str or 'period end' in val_str:
                    for j in range(i+1, len(row.values)):
                        if pd.notna(row.values[j]):
                            period_end = row.values[j]
                            break
    
    # Pattern 2: Check if columns are named 'period_start' and 'period_end'
    if period_start is None:
        for col in metadata_df.columns:
            col_lower = str(col).lower().strip()
            if 'period_start' in col_lower or 'period start' in col_lower:
                period_start = metadata_df[col].dropna().iloc[0] if not metadata_df[col].dropna().empty else None
            elif 'period_end' in col_lower or 'period end' in col_lower:
                period_end = metadata_df[col].dropna().iloc[0] if not metadata_df[col].dropna().empty else None
    
    # Pattern 3: If metadata is a simple key-value structure (2 columns)
    if period_start is None and len(metadata_df.columns) >= 2:
        for idx, row in metadata_df.iterrows():
            key = str(row.iloc[0]).lower().strip() if pd.notna(row.iloc[0]) else ''
            if 'period_start' in key or 'period start' in key:
                period_start = row.iloc[1]
            elif 'period_end' in key or 'period end' in key:
                period_end = row.iloc[1]
    
    print(f"\nExtracted values:")
    print(f"  period_start: {period_start}")
    print(f"  period_end: {period_end}")
    
    if period_start is None or period_end is None:
        print("\nWARNING: Could not find period_start and/or period_end in report_metadata.")
        print("Setting missing values to None/NaN")
    
    # 3. Add the columns to "ledger_master" sheet
    if 'ledger_master' not in all_sheets:
        print("ERROR: 'ledger_master' sheet not found in the Excel file.")
        print(f"Available sheets: {list(all_sheets.keys())}")
        sys.exit(1)
    
    ledger_df = all_sheets['ledger_master']
    print(f"\nOriginal ledger_master sheet ({len(ledger_df)} rows):")
    print(ledger_df.head())
    
    # Add the new columns
    ledger_df['period_start'] = period_start
    ledger_df['period_end'] = period_end
    
    print(f"\nUpdated ledger_master sheet with new columns:")
    print(ledger_df.head())
    
    # Update the sheet in our dictionary
    all_sheets['ledger_master'] = ledger_df
    
    # 4. Save ALL sheets to output Excel file
    print(f"\nSaving all sheets to: {output_excel}")
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        for sheet_name, df in all_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  - Saved sheet: '{sheet_name}' ({len(df)} rows)")
    
    # 5. Save to JSON as well (all sheets)
    print(f"\nSaving to JSON: {output_json}")
    json_output = {}
    for sheet_name, df in all_sheets.items():
        json_output[sheet_name] = df.to_dict(orient='records')
    
    import json
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, default=str)
    
    print(f"\nTransformation complete!")
    print(f"  Excel output: {output_excel}")
    print(f"  JSON output: {output_json}")

if __name__ == "__main__":
    main()