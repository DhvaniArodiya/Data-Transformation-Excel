import pandas as pd
import os
import sys

def main():
    print("=" * 60)
    print("STARTING DATA TRANSFORMATION SCRIPT")
    print("=" * 60)
    
    # Define input and output paths
    input_path = r'temp_uploads\Sample_data.xlsx'
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
    
    # Display original data info
    print("\n" + "-" * 40)
    print("ORIGINAL DATA PREVIEW:")
    print("-" * 40)
    print(df.head())
    print(f"\nData types:\n{df.dtypes}")
    
    # Add Risk_Level column based on high debit transactions
    print("\n" + "-" * 40)
    print("ADDING RISK_LEVEL COLUMN")
    print("-" * 40)
    
    # Check for debit-related columns
    # Common column names that might contain debit information
    debit_columns = [col for col in df.columns if any(keyword in col.lower() for keyword in ['debit', 'amount', 'transaction', 'balance', 'value'])]
    
    print(f"Searching for debit-related columns...")
    print(f"Potential debit columns found: {debit_columns}")
    
    # Initialize Risk_Level column
    df['Risk_Level'] = 'Low'  # Default risk level
    
    if debit_columns:
        # Use the first debit-related column found
        debit_col = debit_columns[0]
        print(f"Using column '{debit_col}' for risk assessment")
        
        # Convert to numeric if possible
        try:
            df[debit_col] = pd.to_numeric(df[debit_col], errors='coerce')
            
            # Calculate thresholds for risk levels
            # High: top 25% of values
            # Medium: 50-75 percentile
            # Low: bottom 50%
            
            if df[debit_col].notna().any():
                q75 = df[debit_col].quantile(0.75)
                q50 = df[debit_col].quantile(0.50)
                
                print(f"Threshold for High Risk (75th percentile): {q75}")
                print(f"Threshold for Medium Risk (50th percentile): {q50}")
                
                # Assign risk levels
                df.loc[df[debit_col] >= q75, 'Risk_Level'] = 'High'
                df.loc[(df[debit_col] >= q50) & (df[debit_col] < q75), 'Risk_Level'] = 'Medium'
                df.loc[df[debit_col] < q50, 'Risk_Level'] = 'Low'
                df.loc[df[debit_col].isna(), 'Risk_Level'] = 'Unknown'
            else:
                print("No valid numeric values found in debit column")
        except Exception as e:
            print(f"Could not process debit column: {e}")
    else:
        # If no debit column found, try to use any numeric column
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if numeric_cols:
            # Use ledger_id or first numeric column for demonstration
            numeric_col = numeric_cols[0]
            print(f"No debit column found. Using '{numeric_col}' for risk assessment demonstration")
            
            if df[numeric_col].notna().any():
                q75 = df[numeric_col].quantile(0.75)
                q50 = df[numeric_col].quantile(0.50)
                
                print(f"Threshold for High Risk (75th percentile): {q75}")
                print(f"Threshold for Medium Risk (50th percentile): {q50}")
                
                df.loc[df[numeric_col] >= q75, 'Risk_Level'] = 'High'
                df.loc[(df[numeric_col] >= q50) & (df[numeric_col] < q75), 'Risk_Level'] = 'Medium'
                df.loc[df[numeric_col] < q50, 'Risk_Level'] = 'Low'
        else:
            print("No numeric columns found. Assigning default 'Low' risk level to all records.")
            print("Note: To properly assess risk, the data should contain debit/transaction amount columns.")
    
    # Display risk level distribution
    print("\n" + "-" * 40)
    print("RISK LEVEL DISTRIBUTION:")
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
        df.to_excel(output_excel, index=False)
        print(f"Successfully saved Excel file: {output_excel}")
    except Exception as e:
        print(f"ERROR saving Excel file: {e}")
    
    # Save to JSON
    try:
        df.to_json(output_json, orient='records', indent=2)
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