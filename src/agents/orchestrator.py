"""
Central Orchestrator - The "Boss"
Manages the complete transformation workflow and state.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
from enum import Enum

from .base_agent import BaseAgent
from .schema_analyst import SchemaAnalystAgent
from .transformation_planner import TransformationPlannerAgent
from .validation_agent import ValidationAgent
from .table_detection_agent import TableDetectionAgent
from .table_matching_agent import TableMatchingAgent
from .code_generation_agent import CodeGenerationAgent

from ..schemas.source_schema import SourceSchemaAnalysis
from ..schemas.target_schema import TargetSchema, get_schema, GENERIC_CUSTOMER_SCHEMA
from ..schemas import additional_schemas  # Ensure schemas are registered
from ..schemas.transformation_plan import TransformationPlan
from ..schemas.validation_report import ValidationReport
from ..schemas.detected_table import MultiTableAnalysis, DetectedTable, TableMatchingResult

from ..engine.execution_engine import ExecutionEngine
from ..utils.excel_loader import ExcelLoader
from ..utils.file_output import FileOutput
from ..config import get_settings


class JobStatus(str, Enum):
    """Status of a transformation job."""
    PENDING = "pending"
    DETECTING_TABLES = "detecting_tables"
    SELECTING_TABLE = "selecting_table"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    WAITING_FOR_INPUT = "waiting_for_input"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class TransformationJob:
    """Represents a single transformation job."""
    
    def __init__(
        self,
        job_id: str,
        source_file: str,
        target_schema_name: str = "generic_customer",
    ):
        self.job_id = job_id
        self.source_file = source_file
        self.target_schema_name = target_schema_name
        self.status = JobStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
        # Results from each stage
        self.source_analysis: Optional[SourceSchemaAnalysis] = None
        self.transformation_plan: Optional[TransformationPlan] = None
        self.validation_report: Optional[ValidationReport] = None
        self.output_file: Optional[str] = None
        
        # User interaction
        self.pending_questions: List[str] = []
        self.user_answers: Dict[str, str] = {}
        
        # Multi-table detection results
        self.multi_table_analysis: Optional[MultiTableAnalysis] = None
        self.table_matching_result: Optional[TableMatchingResult] = None
        self.selected_table_id: Optional[str] = None
        
        # Error tracking
        self.error_message: Optional[str] = None
        self.retry_count: int = 0
        self.max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "job_id": self.job_id,
            "source_file": self.source_file,
            "target_schema_name": self.target_schema_name,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source_analysis": self.source_analysis.model_dump() if self.source_analysis else None,
            "transformation_plan": self.transformation_plan.model_dump() if self.transformation_plan else None,
            "validation_report": self.validation_report.model_dump() if self.validation_report else None,
            "output_file": self.output_file,
            "pending_questions": self.pending_questions,
            "user_answers": self.user_answers,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransformationJob":
        """Create from dictionary."""
        job = cls(
            job_id=data["job_id"],
            source_file=data["source_file"],
            target_schema_name=data.get("target_schema_name", "generic_customer"),
        )
        job.status = JobStatus(data.get("status", "pending"))
        job.created_at = data.get("created_at")
        job.updated_at = data.get("updated_at")
        job.output_file = data.get("output_file")
        job.pending_questions = data.get("pending_questions", [])
        job.user_answers = data.get("user_answers", {})
        job.error_message = data.get("error_message")
        job.retry_count = data.get("retry_count", 0)
        
        # Reconstruct complex objects
        if data.get("validation_report"):
            job.validation_report = ValidationReport(**data["validation_report"])
        if data.get("transformation_plan"):
            job.transformation_plan = TransformationPlan(**data["transformation_plan"])
        
        return job


class Orchestrator:
    """
    Central workflow orchestrator.
    
    Manages the complete transformation pipeline:
    1. Analyze source file
    2. Generate transformation plan
    3. Execute transformations
    4. Validate results
    5. Generate output
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.settings.ensure_directories()
        
        # Initialize agents
        self.table_detector = TableDetectionAgent()
        self.table_matcher = TableMatchingAgent()
        self.schema_analyst = SchemaAnalystAgent()
        self.planner = TransformationPlannerAgent()
        self.validator = ValidationAgent()
        self.code_generator = CodeGenerationAgent()
        self.execution_engine = ExecutionEngine()
    
    def create_job(
        self,
        source_file: str,
        target_schema_name: str = "generic_customer",
    ) -> TransformationJob:
        """
        Create a new transformation job.
        
        Args:
            source_file: Path to source Excel/CSV file
            target_schema_name: Name of target schema
            
        Returns:
            Created TransformationJob
        """
        job_id = str(uuid4())[:8]
        job = TransformationJob(job_id, source_file, target_schema_name)
        self._save_job(job)
        return job
    
    def run_job(self, job: TransformationJob) -> TransformationJob:
        """
        Execute a transformation job through all stages.
        
        Args:
            job: The job to execute
            
        Returns:
            Updated job with results
        """
        try:
            # Stage 0: Detect Tables (if not already done)
            if job.multi_table_analysis is None:
                job = self._stage_detect_tables(job)
                if job.status == JobStatus.FAILED:
                    return job
                if job.status == JobStatus.SELECTING_TABLE:
                    return job  # Need user input to select table
            
            # Stage 1: Analyze
            job = self._stage_analyze(job)
            if job.status == JobStatus.FAILED:
                return job
            
            # Stage 2: Plan
            job = self._stage_plan(job)
            if job.status == JobStatus.WAITING_FOR_INPUT:
                return job
            if job.status == JobStatus.FAILED:
                # Try fallback on planning failure
                return self._stage_fallback_execution(job)
            
            # Check for low confidence -> Fallback
            if job.transformation_plan and job.transformation_plan.confidence_score < 0.5:
                print(f"   ⚠ Low confidence ({job.transformation_plan.confidence_score:.0%}). Switching to fallback.")
                return self._stage_fallback_execution(job)
            
            # Stage 3: Execute
            job = self._stage_execute(job)
            if job.status == JobStatus.FAILED:
                # Try fallback on execution failure
                return self._stage_fallback_execution(job)
            
            # Stage 4: Validate & Output
            job = self._stage_validate_and_output(job)
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
        
        self._save_job(job)
        return job
    
    def _stage_fallback_execution(self, job: TransformationJob) -> TransformationJob:
        """Stage: Fallback to agentic code generation."""
        print(f"⚠ Triggering Agentic Fallback for {job.source_file}...")
        job.status = JobStatus.EXECUTING
        job.updated_at = datetime.now().isoformat()
        
        try:
            target_schema = get_schema(job.target_schema_name)
            if not target_schema:
                raise ValueError(f"Unknown target schema: {job.target_schema_name}")

            # Generate code
            # Ensure we have source analysis
            if not job.source_analysis:
                job.source_analysis = self.schema_analyst.run(job.source_file)
                
            code = self.code_generator.run(
                job.source_file,
                target_schema,
                job.source_analysis
            )
            
            # Save script
            script_path = self.settings.output_dir.parent / f"fallback_{job.job_id}.py"
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            print(f"   ✓ Generated fallback script: {script_path}")
            
            # Execute script
            import subprocess
            import sys
            print("   ⚙️  Executing fallback script...")
            
            result = subprocess.run(
                [sys.executable, str(script_path)], 
                capture_output=True, 
                text=True, 
                cwd=str(self.settings.output_dir.parent)
            )
            
            if result.returncode != 0:
                print(f"   ❌ Execution failed:\n{result.stderr}")
                raise Exception(f"Script execution failed: {result.stderr}")
            
            print("   ✓ Fallback script executed successfully")
            print(result.stdout)
            
            # Check for output file
            expected_output = self.settings.output_dir / f"{target_schema.name}_fallback.xlsx"
            
            if expected_output.exists():
                job.output_file = str(expected_output)
                job.status = JobStatus.COMPLETED
                print(f"   ✓ Output saved: {job.output_file}")
            else:
                 # Check if script generated something else
                 print("   ⚠ Output file not found in expected location")
                 job.status = JobStatus.COMPLETED
                 job.error_message = "Script ran but output file not found at expected location"
                 
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = f"Fallback failed: {str(e)}"
            return job
            
        return job
    
    def _stage_detect_tables(self, job: TransformationJob) -> TransformationJob:
        """Stage 0: Detect tables in source file."""
        print(f"🔍 Stage 0: Detecting tables in {job.source_file}...")
        job.status = JobStatus.DETECTING_TABLES
        job.updated_at = datetime.now().isoformat()
        
        try:
            # Run table detection
            job.multi_table_analysis = self.table_detector.run(job.source_file)
            
            tables = job.multi_table_analysis.tables
            print(f"   ✓ Found {len(tables)} table(s)")
            
            for table in tables:
                title = table.title or f"Row {table.boundary.start_row + 1}"
                print(f"     - {table.table_id}: {title} ({table.row_count} rows, {table.column_count} cols)")
            
            # If single table, auto-select
            if len(tables) == 1:
                job.selected_table_id = tables[0].table_id
                print(f"   ✓ Auto-selected: {job.selected_table_id}")
                return job
            
            # If multiple tables, run matching to find best
            target_schema = get_schema(job.target_schema_name) or GENERIC_CUSTOMER_SCHEMA
            job.table_matching_result = self.table_matcher.run(tables, target_schema)
            
            good_matches = job.table_matching_result.get_good_matches()
            
            if len(good_matches) == 1:
                # Single good match, auto-select
                job.selected_table_id = good_matches[0].table_id
                print(f"   ✓ Best match: {job.selected_table_id} ({good_matches[0].match_score:.0%})")
            elif len(good_matches) > 1:
                # Multiple good matches, need user selection
                job.status = JobStatus.SELECTING_TABLE
                job.pending_questions = [job.table_matching_result.user_prompt or "Which table do you want to transform?"]
                print(f"   ❓ Multiple matching tables - user selection required")
                return job
            elif job.table_matching_result.best_match_table_id:
                # No good matches, use best available
                job.selected_table_id = job.table_matching_result.best_match_table_id
                best = job.table_matching_result.get_best_match()
                print(f"   ⚠ Best match: {job.selected_table_id} ({best.match_score:.0%} - low confidence)")
            else:
                # No matches at all
                job.status = JobStatus.FAILED
                job.error_message = "No suitable tables found in file"
                return job
            
        except Exception as e:
            print(f"   ❌ Table detection failed: {str(e)}")
            job.status = JobStatus.FAILED
            job.error_message = f"Table detection failed: {str(e)}"
            return job
        
        return job
    
    def _stage_analyze(self, job: TransformationJob) -> TransformationJob:
        """Stage 1: Analyze source file or selected table."""
        print(f"📊 Stage 1: Analyzing {job.source_file}...")
        job.status = JobStatus.ANALYZING
        job.updated_at = datetime.now().isoformat()
        
        try:
            # If multi-table detection was done, analyze the selected table only
            if job.selected_table_id and job.multi_table_analysis:
                selected_table = job.multi_table_analysis.get_table_by_id(job.selected_table_id)
                
                if selected_table:
                    print(f"   → Analyzing selected table: {job.selected_table_id}")
                    
                    # Extract the selected table as DataFrame
                    loader = ExcelLoader(job.source_file)
                    table_df = loader.extract_table_from_boundary(
                        boundary=selected_table.boundary,
                        header_row_offset=selected_table.header_row,
                    )
                    
                    # Store for later stages
                    job._selected_table_df = table_df
                    
                    # Run analysis on the extracted table (pass as temporary file or use existing flow)
                    # For now, we analyze the full file but use the extracted data later
                    job.source_analysis = self.schema_analyst.run(job.source_file)
                    
                    # Override column count with selected table info
                    job.source_analysis.total_rows = len(table_df)
                    job.source_analysis.total_columns = len(table_df.columns)
                else:
                    # Fallback to full file analysis
                    job.source_analysis = self.schema_analyst.run(job.source_file)
            else:
                job.source_analysis = self.schema_analyst.run(job.source_file)
            
            print(f"   ✓ Found {len(job.source_analysis.columns)} columns, {job.source_analysis.total_rows} rows")
            print(f"   ✓ Quality: {job.source_analysis.overall_quality}")
        except Exception as e:
            print(f"   ❌ Analysis failed: {str(e)}")
            job.status = JobStatus.FAILED
            job.error_message = f"Analysis failed: {str(e)}"
            return job
        
        return job
    
    def _stage_plan(self, job: TransformationJob) -> TransformationJob:
        """Stage 2: Generate transformation plan."""
        print(f"🏗️  Stage 2: Planning transformation...")
        print(f"DEBUG ORCHESTRATOR: Checking schema 'superstore_daily_orders': {get_schema('superstore_daily_orders')}")
        job.status = JobStatus.PLANNING
        job.updated_at = datetime.now().isoformat()
        
        try:
            target_schema = get_schema(job.target_schema_name) or GENERIC_CUSTOMER_SCHEMA
            job.transformation_plan = self.planner.run(
                job.source_analysis,
                target_schema
            )
            
            print(f"   ✓ Generated plan with {len(job.transformation_plan.column_mappings)} mappings")
            print(f"   ✓ Confidence: {job.transformation_plan.confidence_score:.0%}")
            
            if job.transformation_plan.warnings:
                for warning in job.transformation_plan.warnings[:3]:
                    print(f"   ⚠ {warning}")
            
            # Check if user input is needed
            if job.transformation_plan.requires_user_input:
                job.status = JobStatus.WAITING_FOR_INPUT
                job.pending_questions = job.transformation_plan.user_questions
                print(f"   ❓ Waiting for user input: {len(job.pending_questions)} questions")
                return job
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = f"Planning failed: {str(e)}"
            return job
        
        return job
    
    def _stage_execute(self, job: TransformationJob) -> TransformationJob:
        """Stage 3: Execute transformation plan."""
        print(f"⚙️  Stage 3: Executing transformation...")
        job.status = JobStatus.EXECUTING
        job.updated_at = datetime.now().isoformat()
        
        try:
            # Use extracted table if available, otherwise load full file
            if hasattr(job, '_selected_table_df') and job._selected_table_df is not None:
                df = job._selected_table_df
                print(f"   → Using extracted table data")
            else:
                loader = ExcelLoader(job.source_file)
                df = loader.load_full()
            
            # Execute plan
            result_df, errors = self.execution_engine.execute(df, job.transformation_plan)
            
            print(f"   ✓ Transformed {len(result_df)} rows, {len(result_df.columns)} columns")
            
            # Store result for validation
            job._result_df = result_df
            
        except Exception as e:
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                print(f"   ⟳ Retry {job.retry_count}/{job.max_retries}")
                return self._stage_execute(job)
            
            job.status = JobStatus.FAILED
            job.error_message = f"Execution failed: {str(e)}"
            return job
        
        return job
    
    def _stage_validate_and_output(self, job: TransformationJob) -> TransformationJob:
        """Stage 4: Validate and generate output."""
        print(f"🛡️  Stage 4: Validating & generating output...")
        job.status = JobStatus.VALIDATING
        job.updated_at = datetime.now().isoformat()
        
        try:
            result_df = getattr(job, '_result_df', None)
            if result_df is None:
                raise ValueError("No result data to validate")
            
            # Validate
            target_schema = get_schema(job.target_schema_name) or GENERIC_CUSTOMER_SCHEMA
            job.validation_report = self.validator.run(result_df, target_schema)
            
            print(f"   ✓ Quality Score: {job.validation_report.quality_score:.1f}%")
            print(f"   ✓ Status: {job.validation_report.status}")
            
            # Generate output file
            source_name = Path(job.source_file).stem
            output_filename = f"{source_name}_transformed_{job.job_id}.xlsx"
            
            output_handler = FileOutput()
            output_path = output_handler.generate(
                result_df,
                job.validation_report,
                output_filename
            )
            
            job.output_file = str(output_path)
            job.status = JobStatus.COMPLETED
            
            print(f"   ✓ Output saved: {output_path}")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = f"Validation/Output failed: {str(e)}"
            return job
        
        return job
    
    def answer_question(
        self,
        job: TransformationJob,
        question_index: int,
        answer: str
    ) -> TransformationJob:
        """
        Provide an answer to a pending question.
        
        Args:
            job: The job waiting for input
            question_index: Index of the question being answered
            answer: User's answer
            
        Returns:
            Updated job
        """
        # Handle table selection
        if job.status == JobStatus.SELECTING_TABLE:
            return self.select_table(job, answer)
        
        if job.status != JobStatus.WAITING_FOR_INPUT:
            return job
        
        if question_index < len(job.pending_questions):
            question = job.pending_questions[question_index]
            job.user_answers[question] = answer
        
        # Check if all questions answered
        if len(job.user_answers) >= len(job.pending_questions):
            job.pending_questions = []
            # Resume execution
            return self.run_job(job)
        
        return job
    
    def select_table(
        self,
        job: TransformationJob,
        selection: str
    ) -> TransformationJob:
        """
        Select a table from multiple detected tables.
        
        Args:
            job: The job waiting for table selection
            selection: Table number (1-indexed) or table_id
            
        Returns:
            Updated job, resumed if selection is valid
        """
        if job.status != JobStatus.SELECTING_TABLE:
            return job
        
        if not job.multi_table_analysis:
            job.status = JobStatus.FAILED
            job.error_message = "No tables detected for selection"
            return job
        
        tables = job.multi_table_analysis.tables
        
        # Parse selection - could be number or table_id
        try:
            # Try as number first (1-indexed)
            table_idx = int(selection) - 1
            if 0 <= table_idx < len(tables):
                job.selected_table_id = tables[table_idx].table_id
        except ValueError:
            # Try as table_id
            for table in tables:
                if table.table_id == selection:
                    job.selected_table_id = selection
                    break
        
        if not job.selected_table_id:
            # Invalid selection, keep waiting
            print(f"Invalid selection: {selection}. Please try again.")
            return job
        
        # Clear pending questions and resume
        job.pending_questions = []
        print(f"Selected table: {job.selected_table_id}")
        
        # Resume the pipeline
        return self.run_job(job)
    
    def get_job(self, job_id: str) -> Optional[TransformationJob]:
        """Load a job from storage."""
        job_file = self.settings.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            return None
        
        with open(job_file, 'r') as f:
            data = json.load(f)
        
        return TransformationJob.from_dict(data)
    
    def _save_job(self, job: TransformationJob):
        """Save job to file storage."""
        job.updated_at = datetime.now().isoformat()
        job_file = self.settings.jobs_dir / f"{job.job_id}.json"
        
        with open(job_file, 'w') as f:
            json.dump(job.to_dict(), f, indent=2, default=str)
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs with basic info."""
        jobs = []
        for job_file in self.settings.jobs_dir.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    data = json.load(f)
                jobs.append({
                    "job_id": data["job_id"],
                    "status": data["status"],
                    "source_file": data["source_file"],
                    "created_at": data["created_at"],
                })
            except:
                pass
        return sorted(jobs, key=lambda x: x.get("created_at", ""), reverse=True)
