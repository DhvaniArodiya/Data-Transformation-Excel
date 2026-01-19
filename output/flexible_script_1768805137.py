import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("STARTING DATA TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Define input and output paths
    input_path = r'temp_uploads\Corrected_Final_Data.xlsx'
    output_dir = 'output'
    output_excel = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load the Excel file
    print(f"\nLoading data from: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns found: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Display initial data info
    print("\n" + "-" * 40)
    print("INITIAL DATA PREVIEW:")
    print("-" * 40)
    print(df.head())
    print(f"\nData types:\n{df.dtypes}")
    
    # Add Risk_Level column based on high debit transactions
    # Since the schema doesn't show a 'Debit' column, we need to handle this gracefully
    print("\n" + "-" * 40)
    print("ADDING RISK_LEVEL COLUMN")
    print("-" * 40)
    
    # Check for potential debit-related columns
    debit_columns = [col for col in df.columns if 'debit' in col.lower() or 'amount' in col.lower() or 'transaction' in col.lower()]
    
    if debit_columns:
        print(f"Found potential debit-related columns: {debit_columns}")
        # Use the first debit-related column found
        debit_col = debit_columns[0]
        print(f"Using column '{debit_col}' for Risk_Level calculation")
        
        # Convert to numeric, handling any non-numeric values
        df[debit_col] = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
        
        # Calculate thresholds for risk levels
        q75 = df[debit_col].quantile(0.75)
        q50 = df[debit_col].quantile(0.50)
        
        print(f"Thresholds - High (>75th percentile): {q75}, Medium (>50th percentile): {q50}")
        
        # Assign Risk_Level based on debit transaction amounts
        def assign_risk(value):
            if value >= q75:
                return 'High'
            elif value >= q50:
                return 'Medium'
            else:
                return 'Low'
        
        df['Risk_Level'] = df[debit_col].apply(assign_risk)
        
    else:
        print("No debit-related columns found in the dataset.")
        print("Available columns:", list(df.columns))
        print("\nAssigning Risk_Level based on Industry type as alternative approach:")
        
        # Alternative: Assign risk based on Industry type or other available data
        # Define high-risk industries (example categorization)
        high_risk_industries = ['Finance', 'Banking', 'Insurance', 'Investment', 'Crypto']
        medium_risk_industries = ['Technology', 'Healthcare', 'Real Estate', 'Manufacturing']
        
        def assign_risk_by_industry(industry):
            if pd.isna(industry):
                return 'Unknown'
            industry_str = str(industry).strip()
            if any(hr.lower() in industry_str.lower() for hr in high_risk_industries):
                return 'High'
            elif any(mr.lower() in industry_str.lower() for mr in medium_risk_industries):
                return 'Medium'
            else:
                return 'Low'
        
        if 'Industry' in df.columns:
            df['Risk_Level'] = df['Industry'].apply(assign_risk_by_industry)
            print("Risk_Level assigned based on Industry classification")
        else:
            # If no suitable column exists, assign default risk level
            df['Risk_Level'] = 'Medium'
            print("No suitable column for risk assessment. Assigned default 'Medium' risk level.")
    
    # Display Risk_Level distribution
    print("\n" + "-" * 40)
    print("RISK_LEVEL DISTRIBUTION:")
    print("-" * 40)
    print(df['Risk_Level'].value_counts())
    
    # Display transformed data preview
    print("\n" + "-" * 40)
    print("TRANSFORMED DATA PREVIEW:")
    print("-" * 40)
    print(df.head(10))
    
    # Save to Excel
    print("\n" + "-" * 40)
    print("SAVING OUTPUT FILES")
    print("-" * 40)
    
    try:
        df.to_excel(output_excel, index=False, engine='openpyxl')
        print(f"Successfully saved Excel file: {output_excel}")
    except Exception as e:
        print(f"ERROR saving Excel file: {e}")
    
    # Save to JSON
    try:
        df.to_json(output_json, orient='records', indent=2, force_ascii=False)
        print(f"Successfully saved JSON file: {output_json}")
    except Exception as e:
        print(f"ERROR saving JSON file: {e}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print(f"Total rows processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"New column added: Risk_Level")
    print("=" * 60)

if __name__ == "__main__":
    main()