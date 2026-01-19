"""
Simple Transformation Runner for Customer Data
Transforms Excel data to CSV with enriched columns
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents import Orchestrator
from custom_customer_schema import CUSTOM_CUSTOMER_SCHEMA
from src.schemas.additional_schemas import SCHEMA_REGISTRY

# Register schema
SCHEMA_REGISTRY["custom_customer"] = CUSTOM_CUSTOMER_SCHEMA


def main():
    print("=" * 80)
    print("🤖 Excel to CSV Transformation")
    print("=" * 80)
    
    source_file = "sample_customer_data.xlsx"
    target_schema = "custom_customer"
    
    print(f"\n📂 Source: {source_file}")
    print(f"🎯 Target: {target_schema}\n")
    
    # Create and run job
    orchestrator = Orchestrator()
    job = orchestrator.create_job(source_file, target_schema)
    print(f"Job ID: {job.job_id}\n")
    
    job = orchestrator.run_job(job)
    
    print("\n" + "=" * 80)
    print("📊 RESULTS")
    print("=" * 80)
    print(f"\nStatus: {job.status}")
    
    if job.error_message:
        print(f"\n❌ Error: {job.error_message}")
    
    if job.output_file:
        print(f"\n✅ Output: {job.output_file}")
        
        # Show sample
        try:
            import pandas as pd
            df = pd.read_csv(job.output_file) if str(job.output_file).endswith('.csv') else pd.read_excel(job.output_file)
            print(f"\n📋 Columns ({len(df.columns)}): {list(df.columns)}")
            print(f"\n📊 Sample Data (first 3 rows):\n")
            print(df.head(3).to_string(index=False))
        except Exception as e:
            print(f"\n⚠️  Could not read output: {e}")
    
    return job


if __name__ == "__main__":
    main()
