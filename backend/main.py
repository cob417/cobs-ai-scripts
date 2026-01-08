"""
FastAPI main application
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import logging
import re
import json
from pathlib import Path

from database import init_db, get_db, Job, JobRun
from schemas import (
    JobCreate, JobUpdate, JobResponse, JobRunResponse,
    CronParseRequest, CronParseResponse, StatusResponse
)
from scheduler import (
    add_job_to_scheduler, remove_job_from_scheduler,
    update_job_in_scheduler, start_scheduler, stop_scheduler,
    get_scheduler_status, execute_job
)
from cron_parser import parse_cron_expression

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Cob's AI Scripts API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Database initialized")
    
    # Start scheduler with database session
    db = next(get_db())
    try:
        start_scheduler(db)
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
    logger.info("Scheduler stopped")


# Helper function to generate prompt filename from job name
def generate_prompt_filename(job_name: str) -> str:
    """Generate a valid filename from job name"""
    # Remove invalid characters and replace spaces with hyphens
    filename = re.sub(r'[^\w\s-]', '', job_name)
    filename = re.sub(r'[-\s]+', '-', filename)
    filename = filename.lower().strip('-')
    return f"{filename}.md"


# API Routes

@app.get("/api/status", response_model=StatusResponse)
async def get_status(db: Session = Depends(get_db)):
    """Get scheduler status"""
    status_info = get_scheduler_status()
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.enabled == True).count()
    
    return StatusResponse(
        scheduler_running=status_info["running"],
        active_jobs_count=active_jobs,
        total_jobs_count=total_jobs
    )


@app.post("/api/cron/parse", response_model=CronParseResponse)
async def parse_cron(request: CronParseRequest):
    """Parse cron expression and return human-readable description"""
    try:
        result = parse_cron_expression(request.cron_expression)
        return CronParseResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(db: Session = Depends(get_db)):
    """List all jobs"""
    jobs = db.query(Job).all()
    result = []
    for job in jobs:
        # Check if job is currently running (has a run with status="running" and no completed_at)
        running_run = db.query(JobRun).filter(
            JobRun.job_id == job.id,
            JobRun.status == "running",
            JobRun.completed_at.is_(None)
        ).first()
        
        # Parse email_recipients from JSON string
        email_recipients = None
        if job.email_recipients:
            try:
                email_recipients = json.loads(job.email_recipients)
            except (json.JSONDecodeError, TypeError):
                email_recipients = []
        
        job_dict = {
            "id": job.id,
            "name": job.name,
            "prompt_filename": job.prompt_filename,
            "prompt_content": job.prompt_content,
            "cron_expression": job.cron_expression,
            "enabled": job.enabled,
            "email_recipients": email_recipients,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "is_running": running_run is not None
        }
        result.append(JobResponse(**job_dict))
    return result


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job details"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if job is currently running
    running_run = db.query(JobRun).filter(
        JobRun.job_id == job.id,
        JobRun.status == "running",
        JobRun.completed_at.is_(None)
    ).first()
    
    # Parse email_recipients from JSON string
    email_recipients = None
    if job.email_recipients:
        try:
            email_recipients = json.loads(job.email_recipients)
        except (json.JSONDecodeError, TypeError):
            email_recipients = []
    
    job_dict = {
        "id": job.id,
        "name": job.name,
        "prompt_filename": job.prompt_filename,
        "prompt_content": job.prompt_content,
        "cron_expression": job.cron_expression,
        "enabled": job.enabled,
        "email_recipients": email_recipients,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "is_running": running_run is not None
    }
    return JobResponse(**job_dict)


@app.post("/api/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, db: Session = Depends(get_db)):
    """Create a new job"""
    # Validate cron expression
    try:
        parse_cron_expression(job_data.cron_expression)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")
    
    # Generate prompt filename
    prompt_filename = generate_prompt_filename(job_data.name)
    
    # Check if name or filename already exists
    existing_job = db.query(Job).filter(
        (Job.name == job_data.name) | (Job.prompt_filename == prompt_filename)
    ).first()
    if existing_job:
        raise HTTPException(status_code=400, detail="Job name or filename already exists")
    
    # Serialize email_recipients to JSON string
    # Always include default email
    DEFAULT_EMAIL = 'christopher.j.obrien@gmail.com'
    recipients = job_data.email_recipients or []
    if DEFAULT_EMAIL not in recipients:
        recipients = [DEFAULT_EMAIL] + recipients
    email_recipients_json = json.dumps(recipients)
    
    # Create job
    job = Job(
        name=job_data.name,
        prompt_filename=prompt_filename,
        prompt_content=job_data.prompt_content,
        cron_expression=job_data.cron_expression,
        enabled=job_data.enabled,
        email_recipients=email_recipients_json
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Prompt is stored in database, no file system operation needed
    logger.info(f"Created job {job.id} with prompt stored in database")
    
    # Add to scheduler if enabled
    if job.enabled:
        add_job_to_scheduler(job, db)
    
    logger.info(f"Created job {job.id}: {job.name}")
    
    # Parse email_recipients from JSON string
    email_recipients = None
    if job.email_recipients:
        try:
            email_recipients = json.loads(job.email_recipients)
        except (json.JSONDecodeError, TypeError):
            email_recipients = []
    
    # Return with is_running status
    job_dict = {
        "id": job.id,
        "name": job.name,
        "prompt_filename": job.prompt_filename,
        "prompt_content": job.prompt_content,
        "cron_expression": job.cron_expression,
        "enabled": job.enabled,
        "email_recipients": email_recipients,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "is_running": False  # New jobs are not running
    }
    return JobResponse(**job_dict)


@app.put("/api/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_data: JobUpdate, db: Session = Depends(get_db)):
    """Update a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update fields
    if job_data.name is not None:
        # Check if new name conflicts
        existing = db.query(Job).filter(Job.name == job_data.name, Job.id != job_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Job name already exists")
        job.name = job_data.name
        # Regenerate filename if name changed
        job.prompt_filename = generate_prompt_filename(job_data.name)
    
    if job_data.prompt_content is not None:
        job.prompt_content = job_data.prompt_content
    
    if job_data.cron_expression is not None:
        # Validate cron expression
        try:
            parse_cron_expression(job_data.cron_expression)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")
        job.cron_expression = job_data.cron_expression
    
    if job_data.enabled is not None:
        job.enabled = job_data.enabled
    
    if job_data.email_recipients is not None:
        # Serialize email_recipients to JSON string
        # Always include default email
        DEFAULT_EMAIL = 'christopher.j.obrien@gmail.com'
        recipients = job_data.email_recipients or []
        if DEFAULT_EMAIL not in recipients:
            recipients = [DEFAULT_EMAIL] + recipients
        job.email_recipients = json.dumps(recipients)
    
    db.commit()
    db.refresh(job)
    
    # Prompt is stored in database, no file system operation needed
    if job_data.prompt_content is not None:
        logger.info(f"Updated prompt content in database for job {job.id}")
    
    # Update scheduler
    update_job_in_scheduler(job, db)
    
    logger.info(f"Updated job {job_id}: {job.name}")
    
    # Check if job is currently running
    running_run = db.query(JobRun).filter(
        JobRun.job_id == job.id,
        JobRun.status == "running",
        JobRun.completed_at.is_(None)
    ).first()
    
    # Parse email_recipients from JSON string
    email_recipients = None
    if job.email_recipients:
        try:
            email_recipients = json.loads(job.email_recipients)
        except (json.JSONDecodeError, TypeError):
            email_recipients = []
    
    # Return with is_running status
    job_dict = {
        "id": job.id,
        "name": job.name,
        "prompt_filename": job.prompt_filename,
        "prompt_content": job.prompt_content,
        "cron_expression": job.cron_expression,
        "enabled": job.enabled,
        "email_recipients": email_recipients,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "is_running": running_run is not None
    }
    return JobResponse(**job_dict)


@app.delete("/api/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove from scheduler
    remove_job_from_scheduler(job_id)
    
    # Delete prompt file
    prompt_file = Path(__file__).parent.parent / "prompts" / job.prompt_filename
    if prompt_file.exists():
        prompt_file.unlink()
    
    # Delete job (cascade will delete runs)
    db.delete(job)
    db.commit()
    
    logger.info(f"Deleted job {job_id}: {job.name}")


@app.post("/api/jobs/{job_id}/run", response_model=JobRunResponse)
async def run_job_manual(job_id: int, db: Session = Depends(get_db)):
    """Manually trigger a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Execute job in background (in production, use background tasks)
    # Note: execute_job gets its own DB session, so we don't pass db
    execute_job(job_id)
    
    # Refresh to get the latest run
    db.refresh(job)
    job_run = db.query(JobRun).filter(JobRun.job_id == job_id).order_by(JobRun.started_at.desc()).first()
    if not job_run:
        raise HTTPException(status_code=500, detail="Job execution failed to create run record")
    
    # Add job name to response
    response = JobRunResponse(
        id=job_run.id,
        job_id=job_run.job_id,
        job_name=job.name,
        status=job_run.status,
        output_content=job_run.output_content,
        html_output_content=job_run.html_output_content,
        log_content=job_run.log_content,
        started_at=job_run.started_at,
        completed_at=job_run.completed_at,
        error_message=job_run.error_message
    )
    
    return response


@app.get("/api/job-runs", response_model=List[JobRunResponse])
async def list_job_runs(limit: int = 50, db: Session = Depends(get_db)):
    """List recent job runs"""
    runs = db.query(JobRun).join(Job).order_by(JobRun.started_at.desc()).limit(limit).all()
    
    # Add job names to responses
    responses = []
    for run in runs:
        responses.append(JobRunResponse(
            id=run.id,
            job_id=run.job_id,
            job_name=run.job.name,
            status=run.status,
            output_content=run.output_content,
            html_output_content=run.html_output_content,
            log_content=run.log_content,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_message=run.error_message
        ))
    
    return responses


@app.get("/api/job-runs/{run_id}", response_model=JobRunResponse)
async def get_job_run(run_id: int, db: Session = Depends(get_db)):
    """Get job run details"""
    run = db.query(JobRun).filter(JobRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Job run not found")
    
    return JobRunResponse(
        id=run.id,
        job_id=run.job_id,
        job_name=run.job.name,
        status=run.status,
        output_content=run.output_content,
        html_output_content=run.html_output_content,
        log_content=run.log_content,
        started_at=run.started_at,
        completed_at=run.completed_at,
        error_message=run.error_message
    )


# Serve frontend static files
try:
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        # React build creates assets in a nested 'static' subfolder
        # Mount the inner static folder at /static to serve JS/CSS correctly
        inner_static = static_path / "static"
        if inner_static.exists():
            app.mount("/static", StaticFiles(directory=str(inner_static)), name="static")
        else:
            # Fallback for legacy structure
            app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Serve favicon from root path (browsers request /favicon.ico by default)
        @app.get("/favicon.ico")
        async def favicon_ico():
            favicon_path = static_path / "favicon.ico"
            if favicon_path.exists():
                return FileResponse(str(favicon_path), media_type="image/x-icon")
            # Fallback to PNG if ICO doesn't exist
            favicon_png = static_path / "favicon.png"
            if favicon_png.exists():
                return FileResponse(str(favicon_png), media_type="image/png")
            raise HTTPException(status_code=404, detail="Favicon not found")
        
        @app.get("/favicon.png")
        async def favicon_png():
            favicon_path = static_path / "favicon.png"
            if favicon_path.exists():
                return FileResponse(str(favicon_path), media_type="image/png")
            raise HTTPException(status_code=404, detail="Favicon not found")
        
        # Serve index.html at root
        @app.get("/")
        async def read_root():
            return FileResponse(str(static_path / "index.html"))
except Exception as e:
    logger.warning(f"Could not mount frontend static files: {e}")
