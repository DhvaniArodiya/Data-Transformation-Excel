import pandas as pd
import glob
import os

# Find most recent output
files = sorted(glob.glob("output/Sample - Superstore_transformed_*.xlsx"), key=os.path.getmtime)
if not files:
    print("No output file found")
    exit(1)

latest = files[-1]
print(f"Checking: {latest}")

df = pd.read_excel(latest)

print(f"Columns found: {list(df.columns)}")

# Check columns
expected = ["full_address", "shipping_days"]
for col in expected:
    if col not in df.columns:
        print(f"❌ Missing column: {col}")
    else:
        # Check values
        sample = df[col].dropna().head(3).tolist()
        print(f"✅ {col} exists. Sample: {sample}")

# Quality Check
if "shipping_days" in df.columns:
    valid_count = df["shipping_days"].notnull().sum()
    print(f"shipping_days populated rows: {valid_count}/{len(df)}")
