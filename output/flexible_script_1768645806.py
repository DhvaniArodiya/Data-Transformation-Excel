import pandas as pd
import os
import sys

def main():
    # Define input and output paths
    input_path = 'temp_uploads/Sample_data.xlsx'
    output_dir = 'output'
    output_xlsx = os.path.join(output_dir, 'flexible_transform_result.xlsx')
    output_json = os.path.join(output_dir, 'flexible_transform_result.json')
    
    print("=" * 60)
    print("STARTING DATA TRANSFORMATION")
    print("=" * 60)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load the Excel file
    print(f"\nLoading data from: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Display original data
    print("\nOriginal Data:")
    print(df.to_string())
    
    # Define the region mapping based on state
    print("\n" + "-" * 60)
    print("APPLYING TRANSFORMATION: Adding 'Region' column")
    print("-" * 60)
    
    # Create region mapping dictionary
    region_mapping = {
        'Maharashtra': 'West',
        'Gujarat': 'West',
        'Karnataka': 'West',
        'Tamilnadu': 'South',
        'Tamil Nadu': 'South',  # Handle potential variations
        'UP': 'North',
        'Uttar Pradesh': 'North'  # Handle potential variations
    }
    
    # Check if 'state' column exists
    if 'state' not in df.columns:
        print("WARNING: 'state' column not found. Looking for similar columns...")
        # Try to find a column that might contain state information
        state_cols = [col for col in df.columns if 'state' in col.lower()]
        if state_cols:
            state_col = state_cols[0]
            print(f"Using column '{state_col}' as state column")
        else:
            print("ERROR: No state column found. Cannot add Region.")
            sys.exit(1)
    else:
        state_col = 'state'
    
    # Apply the region mapping
    # First, let's see unique states in the data
    unique_states = df[state_col].unique()
    print(f"\nUnique states found: {list(unique_states)}")
    
    # Map states to regions, handling case sensitivity and whitespace
    def get_region(state):
        if pd.isna(state):
            return 'Unknown'
        # Clean the state value
        state_clean = str(state).strip()
        # Check direct mapping
        if state_clean in region_mapping:
            return region_mapping[state_clean]
        # Check case-insensitive mapping
        for key, value in region_mapping.items():
            if key.lower() == state_clean.lower():
                return value
        return 'Unknown'
    
    # Add the Region column
    df['Region'] = df[state_col].apply(get_region)
    
    # Log the mapping results
    print("\nRegion mapping applied:")
    for state in unique_states:
        region = get_region(state)
        print(f"  {state} -> {region}")
    
    # Display transformed data
    print("\nTransformed Data:")
    print(df.to_string())
    
    # Save to Excel
    print("\n" + "-" * 60)
    print("SAVING OUTPUT FILES")
    print("-" * 60)
    
    try:
        df.to_excel(output_xlsx, index=False)
        print(f"Successfully saved Excel file: {output_xlsx}")
    except Exception as e:
        print(f"ERROR saving Excel file: {e}")
    
    # Save to JSON
    try:
        df.to_json(output_json, orient='records', indent=2)
        print(f"Successfully saved JSON file: {output_json}")
    except Exception as e:
        print(f"ERROR saving JSON file: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE")
    print("=" * 60)
    print(f"Total rows processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"New column added: 'Region'")
    print(f"\nRegion distribution:")
    print(df['Region'].value_counts().to_string())
    print("\nOutput files:")
    print(f"  - {output_xlsx}")
    print(f"  - {output_json}")

if __name__ == "__main__":
    main()