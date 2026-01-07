#!/usr/bin/env python3
"""
Run AI Script - Generic AI Script Runner
A modular script runner that executes any OpenAI prompt-based script.
Loads prompts from the database, calls OpenAI's API, and saves results to database.
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import utility modules
from utils.logging_utils import setup_logging
from utils.email_utils import send_email
from utils.pushover_utils import send_pushover_notification
from utils.openai_utils import get_openai_client, call_openai

# Database imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))
from database import SessionLocal, Job, JobRun
from utils.markdown_utils import markdown_to_html

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Load environment variables from .env file (in script directory)
load_dotenv(SCRIPT_DIR / ".env")

# Configuration - all paths relative to script directory
LOG_DIR = SCRIPT_DIR / "logs"


def load_prompt_from_db(job_id: int, logger) -> tuple[str, str, list[str]]:
    """Load the prompt and email recipients from the database."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            sys.exit(1)
        logger.info(f"Loaded prompt from database for job: {job.name} ({len(job.prompt_content)} characters)")
        
        # Parse email recipients from JSON string
        email_recipients = []
        if job.email_recipients:
            try:
                email_recipients = json.loads(job.email_recipients)
                if not isinstance(email_recipients, list):
                    email_recipients = []
                logger.info(f"Loaded {len(email_recipients)} email recipient(s) from database")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse email recipients from database: {e}")
                email_recipients = []
        
        return job.prompt_content, job.name, email_recipients
    except Exception as e:
        logger.error(f"Error reading prompt from database: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


def save_results_to_db(job_id: int, content: str, logger) -> None:
    """Save results to the database in the job_run record."""
    db = SessionLocal()
    try:
        # Find the most recent running job run for this job
        job_run = db.query(JobRun).filter(
            JobRun.job_id == job_id,
            JobRun.status == "running",
            JobRun.completed_at.is_(None)
        ).order_by(JobRun.started_at.desc()).first()
        
        if not job_run:
            logger.warning("No running job run found to save results to")
            return
        
        # Convert markdown to HTML
        html_content = None
        try:
            html_content = markdown_to_html(content)
            logger.info(f"Converted markdown to HTML ({len(html_content)} characters)")
        except Exception as e:
            logger.warning(f"Failed to convert markdown to HTML: {e}")
        
        # Update the job run with output
        job_run.output_content = content
        job_run.html_output_content = html_content
        db.commit()
        
        logger.info(f"Results saved successfully to database (job_run_id: {job_run.id})")
    except Exception as e:
        logger.error(f"Error saving results to database: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run AI Script - Execute OpenAI prompt-based scripts from database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --job-id 1                        # Run job with ID 1 from database
        """
    )
    parser.add_argument(
        "--job-id",
        type=int,
        required=True,
        help="Job ID from database to execute"
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    # Parse command-line arguments
    args = parse_arguments()
    job_id = args.job_id
    
    # Load job and prompt from database
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"Error: Job {job_id} not found in database.", file=sys.stderr)
            sys.exit(1)
        
        job_name = job.name
        prompt_name = job.prompt_filename.replace('.md', '')
    finally:
        db.close()
    
    # Setup logging
    logger = setup_logging(LOG_DIR, prompt_name)
    
    logger.info("=" * 60)
    logger.info(f"{job_name} Script")
    logger.info(f"Job ID: {job_id}")
    logger.info("=" * 60)
    
    error_details = None
    success = False
    
    try:
        # Load prompt and email recipients from database
        prompt, job_name, email_recipients = load_prompt_from_db(job_id, logger)
        
        # Initialize OpenAI client
        client = get_openai_client(logger)
        
        # Call OpenAI API
        # Get model and web search settings from environment
        openai_model = os.getenv("OPENAI_MODEL", "gpt-5.2")
        enable_web_search = os.getenv("WEB_SEARCH", "true").lower() == "true"
        results = call_openai(client, prompt, logger, model=openai_model, enable_web_search=enable_web_search)
        
        # Save results to database
        save_results_to_db(job_id, results, logger)
        
        # Send email to all recipients (if any are configured)
        if email_recipients:
            for recipient in email_recipients:
                try:
                    send_email(results, recipient, prompt_name, logger)
                    logger.info(f"Email sent successfully to: {recipient}")
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient}: {e}", exc_info=True)
        else:
            logger.info("No email recipients configured for this job. Skipping email.")
        
        logger.info("=" * 60)
        logger.info("Script completed successfully!")
        logger.info("=" * 60)
        
        # Success - prepare success message
        success = True
        message = f"Job completed successfully!\n\nResults saved to database."
        if email_recipients:
            message += f"\nEmail sent to: {', '.join(email_recipients)}"
        
    except SystemExit as e:
        # SystemExit from sys.exit() calls - extract error details
        error_details = "Script exited with an error. Check logs for details."
        logger.error("Script execution failed")
        message = f"Job failed to complete.\n\nError: {error_details}\n\nPlease check the log file for detailed error information."
        
    except Exception as e:
        # Unexpected exception
        error_details = str(e)
        logger.error(f"Unexpected error in main execution: {e}", exc_info=True)
        message = f"Job failed with an unexpected error.\n\nError: {error_details}\n\nPlease check the log file for detailed error information."
    
    finally:
        # Always send Pushover notification
        send_pushover_notification(success, job_name, message, logger)
        
        # If there was an error, exit with error code
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
