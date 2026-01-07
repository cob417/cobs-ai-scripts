#!/usr/bin/env python3
"""
Run AI Script - Generic AI Script Runner
A modular script runner that executes any OpenAI prompt-based script.
Loads prompts from the prompts/ directory, calls OpenAI's API, and saves/emails results.
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import utility modules
from utils.logging_utils import setup_logging
from utils.email_utils import send_email
from utils.pushover_utils import send_pushover_notification
from utils.openai_utils import get_openai_client, call_openai

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Load environment variables from .env file (in script directory)
load_dotenv(SCRIPT_DIR / ".env")

# Configuration - all paths relative to script directory
PROMPTS_DIR = SCRIPT_DIR / "prompts"
DEFAULT_PROMPT_FILE = PROMPTS_DIR / "ai-research-prompt.md"
OUTPUT_DIR = SCRIPT_DIR / "data"
LOG_DIR = SCRIPT_DIR / "logs"
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")


def load_prompt(prompt_file: Path, logger) -> str:
    """Load the prompt from the markdown file."""
    try:
        logger.info(f"Loading prompt from {prompt_file.name}...")
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Prompt loaded successfully ({len(content)} characters)")
        return content
    except FileNotFoundError:
        logger.error(f"Prompt file '{prompt_file}' not found.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading prompt file: {e}", exc_info=True)
        sys.exit(1)


def save_results(content: str, output_dir: Path, prompt_name: str, logger) -> str:
    """Save results to a dated file in the output directory."""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with current date and time (hours, minutes, seconds)
    ts = datetime.now().strftime(f"%Y-%m-%d {prompt_name} %H%M%S")
    filename = f"{ts}.md"
    filepath = output_dir / filename
    
    # Save to file (content is already formatted as markdown by OpenAI)
    logger.info(f"Saving results to {filename}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Results saved successfully to: {filepath}")
    return str(filepath)


def get_prompt_name(prompt_file: Path) -> str:
    """Extract prompt name from file (filename without extension)."""
    return prompt_file.stem


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run AI Script - Execute OpenAI prompt-based scripts with customizable prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s                                    # Use default prompt: {DEFAULT_PROMPT_FILE.name}
  %(prog)s -p my-custom-prompt.md            # Use custom prompt from prompts/ directory
  %(prog)s --prompt prompts/my-prompt.md     # Use full path to prompt file
        """
    )
    parser.add_argument(
        "-p", "--prompt",
        type=str,
        default=None,
        help=f"Prompt file to use (default: {DEFAULT_PROMPT_FILE.name}). "
             f"Can be a filename in the prompts/ directory or a full path."
    )
    return parser.parse_args()


def resolve_prompt_file(prompt_arg: str = None) -> Path:
    """Resolve the prompt file path from command-line argument or use default."""
    if prompt_arg is None:
        # Use default prompt file
        prompt_file = DEFAULT_PROMPT_FILE
    else:
        # Check if it's a full path
        if os.path.isabs(prompt_arg) or "/" in prompt_arg or "\\" in prompt_arg:
            prompt_file = Path(prompt_arg)
        else:
            # Assume it's a filename in the prompts directory
            prompt_file = PROMPTS_DIR / prompt_arg
    
    # Validate that the file exists
    if not prompt_file.exists():
        print(f"Error: Prompt file not found: {prompt_file}", file=sys.stderr)
        print(f"Available prompts in {PROMPTS_DIR}:", file=sys.stderr)
        if PROMPTS_DIR.exists():
            for p in sorted(PROMPTS_DIR.glob("*.md")):
                print(f"  - {p.name}", file=sys.stderr)
        sys.exit(1)
    
    return prompt_file


def main():
    """Main execution function."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Resolve prompt file
    prompt_file = resolve_prompt_file(args.prompt)
    
    # Extract prompt name from file (without extension)
    prompt_name = get_prompt_name(prompt_file)
    
    # Job name for notifications (use prompt name, configurable via JOB_NAME env var)
    job_name = os.getenv("JOB_NAME", prompt_name)
    
    # Setup logging first (needs prompt_name)
    logger = setup_logging(LOG_DIR, prompt_name)
    
    logger.info("=" * 60)
    logger.info(f"{job_name} Script")
    logger.info(f"Using prompt file: {prompt_file.name}")
    logger.info("=" * 60)
    
    error_details = None
    success = False
    
    try:
        # Load prompt
        prompt = load_prompt(prompt_file, logger)
        
        # Initialize OpenAI client
        client = get_openai_client(logger)
        
        # Call OpenAI API
        # Get model and web search settings from environment
        openai_model = os.getenv("OPENAI_MODEL", "gpt-5.2")
        enable_web_search = os.getenv("WEB_SEARCH", "true").lower() == "true"
        results = call_openai(client, prompt, logger, model=openai_model, enable_web_search=enable_web_search)
        
        # Save results
        filepath = save_results(results, OUTPUT_DIR, prompt_name, logger)
        
        # Send email (if recipient is configured)
        if EMAIL_RECIPIENT:
            send_email(results, EMAIL_RECIPIENT, prompt_name, logger)
        else:
            logger.warning("EMAIL_RECIPIENT not set in .env file. Skipping email.")
        
        logger.info("=" * 60)
        logger.info("Script completed successfully!")
        logger.info("=" * 60)
        
        # Success - prepare success message
        success = True
        message = f"Job completed successfully!\n\nResults saved to: {Path(filepath).name}"
        if EMAIL_RECIPIENT:
            message += f"\nEmail sent to: {EMAIL_RECIPIENT}"
        
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
