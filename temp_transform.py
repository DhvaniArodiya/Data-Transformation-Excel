"""
Temporary script to transform Sample - Superstore.xls
- Combines Country, City, State into a single Address column
- Calculates the difference between Order Date and Ship Date
"""
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 60)
    print("📊 Sample - Superstore Transformation")
    print("=" * 60)
    
    # Load the Excel file
    source_file = Path("Sample - Superstore.xls")
    print(f"\n📂 Loading: {source_file}")
    
    df = pd.read_excel(source_file)
    print(f"   ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Display original columns
    print(f"\n📋 Original Columns: {list(df.columns)}")
    
    # Show sample of relevant columns
    print("\n🔍 Sample of original data:")
    print(df[['City', 'State', 'Country', 'Order Date', 'Ship Date']].head(5).to_string())
    
    # ========================================
    # TRANSFORMATION 1: Combine address fields
    # ========================================
    print("\n" + "=" * 60)
    print("🏠 Transformation 1: Creating Full Address")
    print("=" * 60)
    
    # Combine City, State, Country into a single address
    df['Full Address'] = df['City'] + ', ' + df['State'] + ', ' + df['Country']
    print(f"   ✓ Created 'Full Address' column")
    print(f"\n   Sample addresses:")
    for addr in df['Full Address'].head(5):
        print(f"      • {addr}")
    
    # ========================================
    # TRANSFORMATION 2: Date difference
    # ========================================
    print("\n" + "=" * 60)
    print("📅 Transformation 2: Calculating Shipping Days")
    print("=" * 60)
    
    # Convert to datetime if needed
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Ship Date'] = pd.to_datetime(df['Ship Date'])
    
    # Calculate difference in days
    df['Shipping Days'] = (df['Ship Date'] - df['Order Date']).dt.days
    print(f"   ✓ Created 'Shipping Days' column")
    
    # Statistics
    print(f"\n   📈 Shipping Days Statistics:")
    print(f"      • Min: {df['Shipping Days'].min()} days")
    print(f"      • Max: {df['Shipping Days'].max()} days")
    print(f"      • Average: {df['Shipping Days'].mean():.1f} days")
    print(f"      • Most Common: {df['Shipping Days'].mode().values[0]} days")
    
    # Distribution
    print(f"\n   📊 Shipping Days Distribution:")
    dist = df['Shipping Days'].value_counts().sort_index()
    for days, count in dist.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"      {days} days: {count:5d} ({pct:5.1f}%) {bar}")
    
    # ========================================
    # OUTPUT
    # ========================================
    print("\n" + "=" * 60)
    print("💾 Saving Transformed Data")
    print("=" * 60)
    
    # Select output columns
    output_columns = [
        'Row ID', 'Order ID', 'Order Date', 'Ship Date', 'Shipping Days',
        'Full Address', 'City', 'State', 'Country',
        'Customer Name', 'Product Name', 'Sales', 'Quantity', 'Profit'
    ]
    
    # Filter to columns that exist
    output_columns = [col for col in output_columns if col in df.columns]
    output_df = df[output_columns]
    
    # Save to new Excel file
    output_file = Path("output/Superstore_Transformed.xlsx")
    output_file.parent.mkdir(exist_ok=True)
    output_df.to_excel(output_file, index=False)
    
    print(f"   ✓ Saved to: {output_file}")
    print(f"   ✓ Output rows: {len(output_df)}")
    print(f"   ✓ Output columns: {list(output_columns)}")
    
    # Show sample output
    print("\n📊 Sample of Transformed Data:")
    print(output_df[['Order ID', 'Full Address', 'Shipping Days', 'Customer Name']].head(10).to_string())
    
    print("\n" + "=" * 60)
    print("✅ Transformation Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
