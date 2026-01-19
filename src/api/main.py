"""
FastAPI REST API for AI Excel Transformation System.

Endpoints:
- POST /api/transform - Start a transformation job
- GET /api/status/{job_id} - Get job status
- GET /api/question/{job_id} - Get pending questions
- POST /api/answer/{job_id} - Answer a question
- GET /api/jobs - List all jobs
- GET /api/download/{job_id} - Download output file
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.orchestrator import Orchestrator, TransformationJob, JobStatus
from src.config import get_settings


# Initialize FastAPI app
app = FastAPI(
    title="AI Excel Transformation API",
    description="Transform messy Excel files into standardized enterprise formats using AI",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = Orchestrator()
settings = get_settings()


# ============= Request/Response Models =============

class TransformRequest(BaseModel):
    """Request to start a transformation."""
    target_schema: str = "generic_customer"


class TransformResponse(BaseModel):
    """Response after starting a transformation."""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    source_file: str
    target_schema: str
    created_at: str
    updated_at: str
    quality_score: Optional[float] = None
    output_file: Optional[str] = None
    error_message: Optional[str] = None


class QuestionResponse(BaseModel):
    """Pending questions response."""
    job_id: str
    status: str
    questions: List[str]
    answered: int
    total: int


class AnswerRequest(BaseModel):
    """Answer to a question."""
    question_index: int
    answer: str


class JobListItem(BaseModel):
    """Job list item."""
    job_id: str
    status: str
    source_file: str
    created_at: str


# ============= Background Tasks =============

def run_transformation_background(job_id: str):
    """Run transformation in background."""
    job = orchestrator.get_job(job_id)
    if job:
        orchestrator.run_job(job)


# ============= API Endpoints =============

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AI Excel Transformation API",
        "version": "1.0.0",
        "endpoints": {
            "transform": "POST /api/transform",
            "status": "GET /api/status/{job_id}",
            "questions": "GET /api/question/{job_id}",
            "answer": "POST /api/answer/{job_id}",
            "jobs": "GET /api/jobs",
            "download": "GET /api/download/{job_id}",
        }
    }


@app.post("/api/transform", response_model=TransformResponse)
async def transform_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_schema: str = "generic_customer",
):
    """
    Start a new transformation job.
    
    Upload an Excel/CSV file and start the transformation process.
    The transformation runs in the background.
    """
    # Validate file type
    allowed_extensions = {'.xlsx', '.xls', '.xlsm', '.csv'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}"
        )
    
    # Save uploaded file
    settings.ensure_directories()
    upload_dir = settings.jobs_dir / "uploads"
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / file.filename
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    
    # Create job
    job = orchestrator.create_job(str(file_path), target_schema)
    
    # Run in background
    background_tasks.add_task(run_transformation_background, job.job_id)
    
    return TransformResponse(
        job_id=job.job_id,
        status=job.status.value,
        message="Transformation started. Use /api/status/{job_id} to check progress."
    )


@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    """Get the status of a transformation job."""
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    quality_score = None
    if job.validation_report:
        quality_score = job.validation_report.quality_score
    
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        source_file=Path(job.source_file).name,
        target_schema=job.target_schema_name,
        created_at=job.created_at,
        updated_at=job.updated_at,
        quality_score=quality_score,
        output_file=Path(job.output_file).name if job.output_file else None,
        error_message=job.error_message,
    )


@app.get("/api/question/{job_id}", response_model=QuestionResponse)
async def get_questions(job_id: str):
    """Get pending questions for a job waiting for user input."""
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return QuestionResponse(
        job_id=job.job_id,
        status=job.status.value,
        questions=job.pending_questions,
        answered=len(job.user_answers),
        total=len(job.pending_questions),
    )


@app.post("/api/answer/{job_id}")
async def answer_question(
    job_id: str,
    answer: AnswerRequest,
    background_tasks: BackgroundTasks,
):
    """Answer a pending question and resume the job."""
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job.status != JobStatus.WAITING_FOR_INPUT:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not waiting for input (status: {job.status.value})"
        )
    
    # Answer the question
    job = orchestrator.answer_question(job, answer.question_index, answer.answer)
    
    # If resumed, continue in background
    if job.status != JobStatus.WAITING_FOR_INPUT:
        background_tasks.add_task(run_transformation_background, job.job_id)
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": "Answer recorded",
        "remaining_questions": len(job.pending_questions) - len(job.user_answers),
    }


@app.get("/api/jobs", response_model=List[JobListItem])
async def list_jobs():
    """List all transformation jobs."""
    jobs = orchestrator.list_jobs()
    
    return [
        JobListItem(
            job_id=j["job_id"],
            status=j["status"],
            source_file=Path(j["source_file"]).name,
            created_at=j["created_at"],
        )
        for j in jobs
    ]


@app.get("/api/download/{job_id}")
async def download_output(job_id: str):
    """Download the output file for a completed job."""
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed (status: {job.status.value})"
        )
    
    if not job.output_file or not Path(job.output_file).exists():
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=job.output_file,
        filename=Path(job.output_file).name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/api/report/{job_id}")
async def get_report(job_id: str):
    """Get the validation report for a job."""
    job = orchestrator.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    if not job.validation_report:
        raise HTTPException(status_code=400, detail="No validation report available")
    
    return job.validation_report.model_dump()


# ============= Run Server =============

def start_server():
    """Start the API server."""
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    start_server()
