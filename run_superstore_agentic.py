"""
Agentic Pipeline Runner for Superstore Transformation
Uses the full Data-PipeLiner agentic flow:
  Orchestrator → SchemaAnalyst → TransformationPlanner → ExecutionEngine → ValidationAgent
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents import Orchestrator
from src.schemas.additional_schemas import SUPERSTORE_ORDER_SCHEMA, SCHEMA_REGISTRY


def main():
    print("=" * 70)
    print("🤖 DATA-PIPELINER AGENTIC TRANSFORMATION")
    print("=" * 70)
    print()
    
    # Source file
    source_file = "Sample - Superstore.xls"
    target_schema = "superstore_order"
    
    print(f"📂 Source: {source_file}")
    print(f"🎯 Target Schema: {target_schema}")
    print(f"📋 Schema Description: {SUPERSTORE_ORDER_SCHEMA.description}")
    print()
    
    # Display target schema columns
    print("🎯 Target Schema Columns:")
    for col in SUPERSTORE_ORDER_SCHEMA.columns:
        req = "✓" if col.required else " "
        hint = f" ← {col.transformation_hint}" if col.transformation_hint else ""
        print(f"   [{req}] {col.name} ({col.data_type}){hint}")
    print()
    
    # Initialize the Orchestrator
    print("=" * 70)
    print("🚀 STARTING AGENTIC PIPELINE")
    print("=" * 70)
    print()
    
    orchestrator = Orchestrator()
    
    # Create job
    print("📝 Creating transformation job...")
    job = orchestrator.create_job(source_file, target_schema)
    print(f"   ✓ Job ID: {job.job_id}")
    print(f"   ✓ Status: {job.status}")
    print()
    
    # Run the pipeline
    print("⚙️  Running agentic pipeline...")
    print("-" * 70)
    
    job = orchestrator.run_job(job)
    
    print("-" * 70)
    print()
    
    # Report results
    print("=" * 70)
    print("📊 PIPELINE RESULTS")
    print("=" * 70)
    print()
    
    print(f"🏷️  Final Status: {job.status}")
    
    if job.source_analysis:
        print(f"\n📈 Source Analysis:")
        print(f"   • Columns: {len(job.source_analysis.columns)}")
        print(f"   • Rows: {job.source_analysis.total_rows}")
        print(f"   • Quality: {job.source_analysis.overall_quality}")
    
    if job.transformation_plan:
        print(f"\n🗺️  Transformation Plan:")
        print(f"   • Column Mappings: {len(job.transformation_plan.column_mappings)}")
        print(f"   • Confidence: {job.transformation_plan.confidence_score:.0%}")
        
        if job.transformation_plan.column_mappings:
            print(f"\n   Mappings:")
            for mapping in job.transformation_plan.column_mappings[:10]:
                print(f"      {mapping.source_col} → {mapping.target_col}")
    
    if job.validation_report:
        print(f"\n✅ Validation Report:")
        print(f"   • Quality Score: {job.validation_report.quality_score:.0f}%")
        print(f"   • Successful Rows: {job.validation_report.successful_rows}")
        print(f"   • Failed Rows: {job.validation_report.failed_rows}")
        print(f"   • Errors: {len(job.validation_report.errors)}")
        print(f"   • Status: {job.validation_report.status}")
    
    if job.output_file:
        print(f"\n💾 Output File: {job.output_file}")
    
    if job.error_message:
        print(f"\n❌ Error: {job.error_message}")
    
    if job.pending_questions:
        print(f"\n❓ Pending Questions:")
        for q in job.pending_questions:
            print(f"   • {q}")
    
    print()
    print("=" * 70)
    print("🏁 PIPELINE COMPLETE")
    print("=" * 70)
    
    return job


if __name__ == "__main__":
    main()
