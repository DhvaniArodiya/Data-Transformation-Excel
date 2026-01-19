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
    
    # Load the source file
    print(f"\nLoading source file: {input_path}")
    try:
        df = pd.read_excel(input_path)
        print(f"Successfully loaded {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        sys.exit(1)
    
    # Display original data
    print("\nOriginal Data Preview:")
    print(df.head(10).to_string())
    
    # Define region mapping based on City and State
    # Common US region classifications
    print("\n" + "-" * 60)
    print("ADDING 'Region' COLUMN BASED ON CITY/STATE VALUES")
    print("-" * 60)
    
    # Define state to region mapping (US-based)
    state_to_region = {
        # Northeast
        'CT': 'Northeast', 'ME': 'Northeast', 'MA': 'Northeast', 'NH': 'Northeast',
        'RI': 'Northeast', 'VT': 'Northeast', 'NJ': 'Northeast', 'NY': 'Northeast',
        'PA': 'Northeast', 'Connecticut': 'Northeast', 'Maine': 'Northeast',
        'Massachusetts': 'Northeast', 'New Hampshire': 'Northeast', 'Rhode Island': 'Northeast',
        'Vermont': 'Northeast', 'New Jersey': 'Northeast', 'New York': 'Northeast',
        'Pennsylvania': 'Northeast',
        
        # Southeast
        'AL': 'Southeast', 'AR': 'Southeast', 'FL': 'Southeast', 'GA': 'Southeast',
        'KY': 'Southeast', 'LA': 'Southeast', 'MS': 'Southeast', 'NC': 'Southeast',
        'SC': 'Southeast', 'TN': 'Southeast', 'VA': 'Southeast', 'WV': 'Southeast',
        'Alabama': 'Southeast', 'Arkansas': 'Southeast', 'Florida': 'Southeast',
        'Georgia': 'Southeast', 'Kentucky': 'Southeast', 'Louisiana': 'Southeast',
        'Mississippi': 'Southeast', 'North Carolina': 'Southeast', 'South Carolina': 'Southeast',
        'Tennessee': 'Southeast', 'Virginia': 'Southeast', 'West Virginia': 'Southeast',
        
        # Midwest
        'IL': 'Midwest', 'IN': 'Midwest', 'IA': 'Midwest', 'KS': 'Midwest',
        'MI': 'Midwest', 'MN': 'Midwest', 'MO': 'Midwest', 'NE': 'Midwest',
        'ND': 'Midwest', 'OH': 'Midwest', 'SD': 'Midwest', 'WI': 'Midwest',
        'Illinois': 'Midwest', 'Indiana': 'Midwest', 'Iowa': 'Midwest', 'Kansas': 'Midwest',
        'Michigan': 'Midwest', 'Minnesota': 'Midwest', 'Missouri': 'Midwest',
        'Nebraska': 'Midwest', 'North Dakota': 'Midwest', 'Ohio': 'Midwest',
        'South Dakota': 'Midwest', 'Wisconsin': 'Midwest',
        
        # Southwest
        'AZ': 'Southwest', 'NM': 'Southwest', 'OK': 'Southwest', 'TX': 'Southwest',
        'Arizona': 'Southwest', 'New Mexico': 'Southwest', 'Oklahoma': 'Southwest', 'Texas': 'Southwest',
        
        # West
        'AK': 'West', 'CA': 'West', 'CO': 'West', 'HI': 'West', 'ID': 'West',
        'MT': 'West', 'NV': 'West', 'OR': 'West', 'UT': 'West', 'WA': 'West', 'WY': 'West',
        'Alaska': 'West', 'California': 'West', 'Colorado': 'West', 'Hawaii': 'West',
        'Idaho': 'West', 'Montana': 'West', 'Nevada': 'West', 'Oregon': 'West',
        'Utah': 'West', 'Washington': 'West', 'Wyoming': 'West',
        
        # DC and Territories
        'DC': 'Northeast', 'District of Columbia': 'Northeast',
        'PR': 'Southeast', 'Puerto Rico': 'Southeast',
    }
    
    # City to region mapping for major cities (fallback)
    city_to_region = {
        'New York': 'Northeast', 'NYC': 'Northeast', 'Boston': 'Northeast',
        'Philadelphia': 'Northeast', 'Pittsburgh': 'Northeast',
        'Los Angeles': 'West', 'LA': 'West', 'San Francisco': 'West',
        'San Diego': 'West', 'Seattle': 'West', 'Portland': 'West',
        'Denver': 'West', 'Phoenix': 'Southwest', 'Las Vegas': 'West',
        'Chicago': 'Midwest', 'Detroit': 'Midwest', 'Minneapolis': 'Midwest',
        'Cleveland': 'Midwest', 'Indianapolis': 'Midwest', 'Milwaukee': 'Midwest',
        'Houston': 'Southwest', 'Dallas': 'Southwest', 'Austin': 'Southwest',
        'San Antonio': 'Southwest', 'Oklahoma City': 'Southwest',
        'Miami': 'Southeast', 'Atlanta': 'Southeast', 'Charlotte': 'Southeast',
        'Nashville': 'Southeast', 'New Orleans': 'Southeast', 'Tampa': 'Southeast',
    }
    
    def determine_region(row):
        """Determine region based on state first, then city as fallback"""
        # Check state column if it exists
        if 'state' in df.columns and pd.notna(row.get('state')):
            state_val = str(row['state']).strip()
            if state_val in state_to_region:
                return state_to_region[state_val]
        
        # Check city column as fallback
        if 'city' in df.columns and pd.notna(row.get('city')):
            city_val = str(row['city']).strip()
            # Check exact match
            if city_val in city_to_region:
                return city_to_region[city_val]
            # Check partial match (case-insensitive)
            for city_key, region in city_to_region.items():
                if city_key.lower() in city_val.lower() or city_val.lower() in city_key.lower():
                    return region
        
        return 'Unknown'
    
    # Apply the region determination
    df['Region'] = df.apply(determine_region, axis=1)
    
    # Log the region distribution
    print("\nRegion Distribution:")
    region_counts = df['Region'].value_counts()
    for region, count in region_counts.items():
        print(f"  {region}: {count} records")
    
    # Display transformed data
    print("\nTransformed Data Preview:")
    print(df.head(10).to_string())
    
    # Save to Excel
    print("\n" + "-" * 60)
    print("SAVING OUTPUT FILES")
    print("-" * 60)
    
    try:
        df.to_excel(output_excel, index=False, engine='openpyxl')
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
    print(f"Total records processed: {len(df)}")
    print(f"Total columns in output: {len(df.columns)}")
    print(f"Output columns: {list(df.columns)}")
    print("=" * 60)

if __name__ == "__main__":
    main()