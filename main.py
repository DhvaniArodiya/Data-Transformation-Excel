"""
AI Excel Transformation System - CLI Entry Point

Usage:
    python main.py transform <file_path> [--schema <schema_name>]
    python main.py status <job_id>
    python main.py list
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.orchestrator import Orchestrator, JobStatus
from src.config import get_settings


def cmd_transform(args):
    """Transform a file."""
    file_path = args.file
    schema_name = args.schema or "generic_customer"
    
    # Validate file exists
    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        return 1
    
    print("=" * 60)
    print("🤖 AI Excel Transformation System")
    print("=" * 60)
    print(f"📁 Source: {file_path}")
    print(f"🎯 Target: {schema_name}")
    print("-" * 60)
    
    # Run transformation
    orchestrator = Orchestrator()
    job = orchestrator.create_job(file_path, schema_name)
    print(f"📋 Job ID: {job.job_id}")
    print("-" * 60)
    
    job = orchestrator.run_job(job)
    
    print("-" * 60)
    
    if job.status == JobStatus.COMPLETED:
        print(f"✅ COMPLETED!")
        print(f"📊 Quality Score: {job.validation_report.quality_score:.1f}%")
        print(f"📄 Output: {job.output_file}")
        return 0
    
    elif job.status == JobStatus.WAITING_FOR_INPUT:
        print(f"❓ WAITING FOR INPUT")
        print("Questions:")
        for i, q in enumerate(job.pending_questions):
            print(f"  {i+1}. {q}")
        print(f"\nUse: python main.py answer {job.job_id} <question_index> <answer>")
        return 0
    
    else:
        print(f"❌ FAILED: {job.error_message}")
        return 1


def cmd_status(args):
    """Check job status."""
    job_id = args.job_id
    
    orchestrator = Orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        print(f"❌ Job not found: {job_id}")
        return 1
    
    print(f"📋 Job: {job.job_id}")
    print(f"📁 Source: {job.source_file}")
    print(f"📊 Status: {job.status.value}")
    
    if job.validation_report:
        print(f"🎯 Quality: {job.validation_report.quality_score:.1f}%")
    
    if job.output_file:
        print(f"📄 Output: {job.output_file}")
    
    if job.error_message:
        print(f"❌ Error: {job.error_message}")
    
    if job.pending_questions:
        print("❓ Pending Questions:")
        for i, q in enumerate(job.pending_questions):
            print(f"  {i+1}. {q}")
    
    return 0


def cmd_list(args):
    """List all jobs."""
    orchestrator = Orchestrator()
    jobs = orchestrator.list_jobs()
    
    if not jobs:
        print("No jobs found.")
        return 0
    
    print(f"{'Job ID':<10} {'Status':<20} {'Source File':<40}")
    print("-" * 70)
    
    for job in jobs:
        job_id = job["job_id"]
        status = job["status"]
        source = Path(job["source_file"]).name[:38]
        print(f"{job_id:<10} {status:<20} {source:<40}")
    
    return 0


def cmd_answer(args):
    """Answer a pending question."""
    job_id = args.job_id
    question_index = int(args.question_index) - 1  # Convert to 0-indexed
    answer = args.answer
    
    orchestrator = Orchestrator()
    job = orchestrator.get_job(job_id)
    
    if not job:
        print(f"❌ Job not found: {job_id}")
        return 1
    
    if job.status != JobStatus.WAITING_FOR_INPUT:
        print(f"❌ Job is not waiting for input (status: {job.status.value})")
        return 1
    
    job = orchestrator.answer_question(job, question_index, answer)
    
    if job.status == JobStatus.COMPLETED:
        print(f"✅ Job completed!")
        print(f"📄 Output: {job.output_file}")
    elif job.status == JobStatus.WAITING_FOR_INPUT:
        print(f"❓ More questions pending")
    else:
        print(f"📊 Status: {job.status.value}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="AI Excel Transformation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py transform data.xlsx
  python main.py transform data.csv --schema generic_customer
  python main.py status abc123
  python main.py list
  python main.py answer abc123 1 "US"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Transform command
    transform_parser = subparsers.add_parser("transform", help="Transform a file")
    transform_parser.add_argument("file", help="Path to Excel/CSV file")
    transform_parser.add_argument(
        "--schema", "-s",
        default="generic_customer",
        help="Target schema name (default: generic_customer)"
    )
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check job status")
    status_parser.add_argument("job_id", help="Job ID to check")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all jobs")
    
    # Answer command
    answer_parser = subparsers.add_parser("answer", help="Answer a pending question")
    answer_parser.add_argument("job_id", help="Job ID")
    answer_parser.add_argument("question_index", help="Question number (1-based)")
    answer_parser.add_argument("answer", help="Your answer")
    
    args = parser.parse_args()
    
    if args.command == "transform":
        return cmd_transform(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "answer":
        return cmd_answer(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
