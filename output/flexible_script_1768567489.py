import pandas as pd
import os
import sys

def main():
    # Define paths
    input_path = r'temp_uploads\Corrected_Final_Data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    print("=" * 60)
    print("STARTING DATA TRANSFORMATION")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[INFO] Created output directory: {output_dir}")
    
    # Load the Excel file
    print(f"\n[INFO] Loading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"[SUCCESS] File loaded successfully!")
        print(f"[INFO] Total rows: {len(df)}")
        print(f"[INFO] Total columns: {len(df.columns)}")
        print(f"[INFO] Columns: {list(df.columns)}")
    except Exception as e:
        print(f"[ERROR] Failed to load file: {e}")
        sys.exit(1)
    
    # Display initial data info
    print("\n[INFO] Initial data preview:")
    print(df.head(3).to_string())
    
    # Define contact columns to check
    contact_columns = ['Primary_Link', 'Secondary_Link', 'Whatsapp', 'Email']
    
    print("\n" + "=" * 60)
    print("ADDING RISK_LEVEL COLUMN")
    print("=" * 60)
    
    def check_risk_level(row):
        """
        Check if contact details are missing or invalid.
        Returns 'High Risk' if any contact detail is missing/invalid.
        """
        issues = []
        
        for col in contact_columns:
            if col in row.index:
                value = row[col]
                
                # Check if value is missing (NaN, None, empty string, whitespace only)
                if pd.isna(value):
                    issues.append(f"{col}: missing")
                elif isinstance(value, str):
                    value_stripped = value.strip()
                    if value_stripped == '' or value_stripped.lower() in ['na', 'n/a', 'none', 'null', '-']:
                        issues.append(f"{col}: invalid")
                    # Additional validation for specific fields
                    elif col == 'Email':
                        # Basic email validation - should contain @ and .
                        if '@' not in value_stripped or '.' not in value_stripped:
                            issues.append(f"{col}: invalid format")
                    elif col == 'Whatsapp':
                        # Basic phone validation - should have some digits
                        digits = ''.join(filter(str.isdigit, value_stripped))
                        if len(digits) < 7:  # Minimum reasonable phone number length
                            issues.append(f"{col}: invalid format")
        
        if issues:
            return 'High Risk'
        else:
            return 'Low Risk'
    
    # Apply the risk level check
    print("[INFO] Analyzing contact details for each row...")
    df['Risk_Level'] = df.apply(check_risk_level, axis=1)
    
    # Count and display statistics
    risk_counts = df['Risk_Level'].value_counts()
    print("\n[INFO] Risk Level Distribution:")
    for level, count in risk_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  - {level}: {count} rows ({percentage:.1f}%)")
    
    # Show details of missing/invalid data per column
    print("\n[INFO] Missing/Invalid data per contact column:")
    for col in contact_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            empty_count = df[col].apply(lambda x: isinstance(x, str) and x.strip() == '').sum()
            total_issues = missing_count + empty_count
            print(f"  - {col}: {total_issues} issues ({missing_count} missing, {empty_count} empty)")
    
    # Display sample of high risk entries
    high_risk_df = df[df['Risk_Level'] == 'High Risk']
    if len(high_risk_df) > 0:
        print(f"\n[INFO] Sample of High Risk entries (first 3):")
        print(high_risk_df.head(3).to_string())
    
    # Save to Excel
    print("\n" + "=" * 60)
    print("SAVING OUTPUT FILES")
    print("=" * 60)
    
    try:
        df.to_excel(output_xlsx, index=False, engine='openpyxl')
        print(f"[SUCCESS] Saved Excel file: {output_xlsx}")
    except Exception as e:
        print(f"[ERROR] Failed to save Excel file: {e}")
    
    # Save to JSON
    try:
        df.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"[SUCCESS] Saved JSON file: {output_json}")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"[INFO] Total rows processed: {len(df)}")
    print(f"[INFO] Total columns in output: {len(df.columns)}")
    print(f"[INFO] New column added: 'Risk_Level'")
    print(f"[INFO] Output columns: {list(df.columns)}")
    
    print("\n[INFO] Final data preview (first 5 rows):")
    print(df.head().to_string())

if __name__ == "__main__":
    main()