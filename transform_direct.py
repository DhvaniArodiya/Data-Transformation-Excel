"""
Direct Excel to CSV Transformation Script
Transforms sample_customer_data.xlsx to CSV with enriched columns:
- Preserves all original columns
- Adds full_name = First Name + Last Name  
- Adds age_at_current = age as of 2025-12-31
"""
import pandas as pd
from datetime import datetime
from pathlib import Path

def main():
    print("=" * 80)
    print("🤖 Excel to CSV Transformation (Direct Mode)")
    print("=" * 80)
    
    # Source file
    source_file = "sample_customer_data.xlsx"
    
    print(f"\n📂 Reading: {source_file}")
    
    # Read Excel
    df = pd.read_excel(source_file)
    
    print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"   📋 Columns: {list(df.columns)}")
    
    # Add full_name column
    print("\n⚙️  Adding computed columns...")
    df['full_name'] = df['First Name'] + ' ' + df['Last Name']
    print("   ✅ Added 'full_name' = First Name + Last Name")
    
    # Add age_at_current column
    # Current date: 2025-12-31
    current_date = datetime(2025, 12, 31)
    
    # Parse the Date column (format: DD/MM/YYYY)
    df['Date_parsed'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    
    # Calculate years difference
    df['years_elapsed'] = (current_date - df['Date_parsed']).dt.days // 365
    
    # Calculate age_at_current
    df['age_at_current'] = df['Age'] + df['years_elapsed']
    
    print("   ✅ Added 'age_at_current' = Age + years since Date")
    
    # Drop temporary columns
    df = df.drop(columns=['Date_parsed', 'years_elapsed'])
    
    # Reorder columns: original + new computed columns
    column_order = ['First Name', 'Last Name', 'Gender', 'Country', 'Age', 'Date', 'Id', 
                    'full_name', 'age_at_current']
    df = df[column_order]
    
    # Save to CSV
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"sample_customer_data_transformed_{timestamp}.csv"
    
    df.to_csv(output_file, index=False)
    
    print(f"\n💾 Output saved: {output_file}")
    print(f"   ✅ {len(df)} rows, {len(df.columns)} columns")
    
    # Display sample
    print("\n📊 Sample Output (first 3 rows):\n")
    print(df.head(3).to_string(index=False))
    
    print("\n" + "=" * 80)
    print("✅ Transformation Complete!")
    print("=" * 80)
    
    return output_file


if __name__ == "__main__":
    result = main()
    print(f"\n📁 Output file: {result}")
