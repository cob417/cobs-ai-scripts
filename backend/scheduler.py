"""
APScheduler wrapper for executing scheduled jobs
"""

import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from database import Job, JobRun, get_db

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
RUN_SCRIPT = SCRIPT_DIR / "run_ai_script.py"

# Import markdown to HTML converter
sys.path.insert(0, str(SCRIPT_DIR))
from utils.markdown_utils import markdown_to_html

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def execute_job(job_id: int):
    """Execute a job by running run_ai_script.py"""
    # Get a new database session for this job execution
    db = next(get_db())
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        # Create job run record
        job_run = JobRun(
            job_id=job_id,
            status="running",
            started_at=datetime.utcnow()
        )
        db.add(job_run)
        db.commit()
        db.refresh(job_run)
        
        logger.info(f"Starting execution of job {job_id} ({job.name})")
        
        try:
            # Execute the script with job_id (no file system operations needed)
            result = subprocess.run(
                [sys.executable, str(RUN_SCRIPT), "--job-id", str(job_id)],
                capture_output=True,
                text=True,
                cwd=str(SCRIPT_DIR),
                timeout=3600  # 1 hour timeout
            )
            
            # Capture logs (stdout contains log messages)
            log_content = result.stderr + "\n" + result.stdout
            
            # Read output from database (script saves it there)
            output_content = None
            html_output_content = None
            
            if result.returncode == 0:
                # Refresh job_run to get the output that was saved by the script
                db.refresh(job_run)
                output_content = job_run.output_content
                html_output_content = job_run.html_output_content
                
                if output_content:
                    logger.info(f"Retrieved output from database ({len(output_content)} characters)")
                else:
                    logger.warning("No output content found in database, using stdout as fallback")
                    output_content = result.stdout
            else:
                # On failure, use stdout as output
                output_content = result.stdout
            
            # Update job run (output_content and html_output_content already saved by script)
            job_run.status = "success" if result.returncode == 0 else "failed"
            # Only update output if script didn't save it (for error cases)
            if not job_run.output_content:
                job_run.output_content = output_content
            if not job_run.html_output_content and output_content:
                # Try to convert if HTML wasn't saved
                try:
                    job_run.html_output_content = markdown_to_html(output_content)
                except Exception as e:
                    logger.warning(f"Failed to convert output to HTML: {e}")
            job_run.log_content = log_content
            job_run.completed_at = datetime.utcnow()
            
            if result.returncode != 0:
                job_run.error_message = f"Script exited with code {result.returncode}"
                logger.error(f"Job {job_id} failed: {job_run.error_message}")
            else:
                logger.info(f"Job {job_id} completed successfully")
            
        except subprocess.TimeoutExpired:
            job_run.status = "failed"
            job_run.error_message = "Job execution timed out after 1 hour"
            job_run.completed_at = datetime.utcnow()
            logger.error(f"Job {job_id} timed out")
        
        except Exception as e:
            job_run.status = "failed"
            job_run.error_message = str(e)
            job_run.completed_at = datetime.utcnow()
            logger.error(f"Job {job_id} failed with exception: {e}", exc_info=True)
        
        finally:
            db.commit()
    finally:
        db.close()


def add_job_to_scheduler(job: Job, db: Session):
    """Add a job to the scheduler"""
    if not job.enabled:
        logger.info(f"Job {job.id} is disabled, not adding to scheduler")
        return
    
    try:
        # Parse cron expression
        parts = job.cron_expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {job.cron_expression}")
        
        minute, hour, day, month, day_of_week = parts
        
        # Add job to scheduler
        scheduler.add_job(
            execute_job,
            trigger=CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            ),
            id=f"job_{job.id}",
            args=[job.id],
            replace_existing=True
        )
        logger.info(f"Added job {job.id} ({job.name}) to scheduler with cron: {job.cron_expression}")
    
    except Exception as e:
        logger.error(f"Failed to add job {job.id} to scheduler: {e}", exc_info=True)


def remove_job_from_scheduler(job_id: int):
    """Remove a job from the scheduler"""
    try:
        scheduler.remove_job(f"job_{job_id}")
        logger.info(f"Removed job {job_id} from scheduler")
    except Exception as e:
        logger.warning(f"Failed to remove job {job_id} from scheduler: {e}")


def update_job_in_scheduler(job: Job, db: Session):
    """Update a job in the scheduler"""
    remove_job_from_scheduler(job.id)
    if job.enabled:
        add_job_to_scheduler(job, db)


def start_scheduler(db: Session):
    """Start the scheduler and load all enabled jobs"""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return
    
    scheduler.start()
    logger.info("Scheduler started")
    
    # Load all enabled jobs
    jobs = db.query(Job).filter(Job.enabled == True).all()
    for job in jobs:
        add_job_to_scheduler(job, db)


def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    else:
        logger.warning("Scheduler is not running")


def get_scheduler_status():
    """Get scheduler status"""
    return {
        "running": scheduler.running,
        "jobs_count": len(scheduler.get_jobs())
    }
