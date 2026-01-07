#!/usr/bin/env python3
"""
AI News Research Script
Calls OpenAI's latest agentic chat completion model to generate AI news research
and saves/emails the results.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI
from dotenv import load_dotenv

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Load environment variables from .env file (in script directory)
load_dotenv(SCRIPT_DIR / ".env")

# Configuration - all paths relative to script directory
PROMPT_FILE = SCRIPT_DIR / "ai-research-prompt.md"
OUTPUT_DIR = SCRIPT_DIR / "data"
LOG_DIR = SCRIPT_DIR / "logs"
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# OpenAI model - can be overridden via OPENAI_MODEL environment variable
# Default to gpt-5.2 with browsing (best for research tasks)
# For reasoning models, use: o1, o1-preview, o3-preview, o3-mini
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

# Enable web browsing for research tasks (can be disabled via WEB_SEARCH env var)
ENABLE_WEB_SEARCH = os.getenv("WEB_SEARCH", "true").lower() == "true"


def setup_logging(log_dir: Path) -> logging.Logger:
    """Setup logging to a file with naming convention matching data files."""
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with same convention as data files
    ts = datetime.now().strftime("%Y-%m-%d AI News Research %H%M%S")
    log_filename = f"{ts}.log"
    log_filepath = log_dir / log_filename
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Also log to console
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filepath}")
    return logger


def load_prompt(prompt_file: Path, logger: logging.Logger) -> str:
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


def get_openai_client(logger: logging.Logger) -> OpenAI:
    """Initialize and return OpenAI client."""
    logger.info("Initializing OpenAI client...")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set.")
        logger.error("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    logger.info("OpenAI client initialized successfully")
    return OpenAI(api_key=api_key)


def call_openai(client: OpenAI, prompt: str, logger: logging.Logger) -> str:
    """Call OpenAI's Responses API with web browsing if enabled."""
    logger.info(f"Calling OpenAI API with model: {OPENAI_MODEL}...")
    
    try:
        # Use Responses API (same as ChatGPT UI) with web search tool if enabled
        if ENABLE_WEB_SEARCH:
            logger.info("Using Responses API with web browsing enabled...")
            response = client.responses.create(
                model=OPENAI_MODEL,
                input=prompt,
                tools=[{"type": "web_search"}],  # Enable web browsing (same as ChatGPT UI)
                include=["web_search_call.action.sources"],  # Optional: return sources
            )
            logger.info("Web browsing enabled successfully!")
            result = response.output_text
            logger.info(f"OpenAI API call completed successfully ({len(result)} characters returned)")
            return result
        else:
            # Fallback to Chat Completions API if web browsing is disabled
            logger.info("Using Chat Completions API (web browsing disabled)...")
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            result = response.choices[0].message.content
            logger.info(f"OpenAI API call completed successfully ({len(result)} characters returned)")
            return result
    except AttributeError as e:
        # Responses API might not be available in older library versions
        if "responses" in str(e).lower():
            logger.warning("Responses API not available in this OpenAI library version.")
            logger.warning("Falling back to Chat Completions API...")
            logger.warning("To enable web browsing, update: pip install --upgrade openai")
            # Fallback to chat completions
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            result = response.choices[0].message.content
            logger.info(f"Fallback API call completed successfully ({len(result)} characters returned)")
            return result
        else:
            raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        
        # Provide helpful suggestions for common errors
        if "model" in error_msg.lower() and ("not exist" in error_msg.lower() or "not found" in error_msg.lower()):
            logger.error("\nSuggested fixes:")
            logger.error("1. Check if the model name is correct. Available models include:")
            logger.error("   - gpt-5.2 (recommended for research with web browsing)")
            logger.error("   - gpt-4o (widely available, no browsing)")
            logger.error("   - gpt-4-turbo")
            logger.error("   - gpt-4")
            logger.error("2. Set OPENAI_MODEL in your .env file, e.g.:")
            logger.error("   OPENAI_MODEL=gpt-5.2")
            logger.error("3. To enable web browsing:")
            logger.error("   - Update OpenAI library: pip install --upgrade openai")
            logger.error("   - Ensure your account has Responses API access")
            logger.error("   - Set WEB_SEARCH=true in .env (default)")
        elif "responses" in error_msg.lower():
            logger.warning("\nNote: Responses API may require:")
            logger.warning("   - Updated OpenAI library: pip install --upgrade openai")
            logger.warning("   - Account access to Responses API")
            logger.warning("   - Falling back to Chat Completions API without browsing...")
            # Try fallback
            try:
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                )
                result = response.choices[0].message.content
                logger.info(f"Fallback API call completed successfully ({len(result)} characters returned)")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}", exc_info=True)
                sys.exit(1)
        
        sys.exit(1)


def save_results(content: str, output_dir: Path, logger: logging.Logger) -> str:
    """Save results to a dated file in the output directory."""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with current date and time (hours, minutes, seconds)
    ts = datetime.now().strftime("%Y-%m-%d AI News Research %H%M%S")
    filename = f"{ts}.md"
    filepath = output_dir / filename
    
    # Save to file
    logger.info(f"Saving results to {filename}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Results saved successfully to: {filepath}")
    return str(filepath)


def send_email(content: str, recipient: str, logger: logging.Logger, subject: str = None):
    """Send email with the research results."""
    if subject is None:
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"AI News Research - {today}"
    
    # Get email configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    if not email_user or not email_password:
        logger.warning("Email credentials not configured.")
        logger.warning("Set EMAIL_USER and EMAIL_PASSWORD environment variables to enable email.")
        logger.warning("For Gmail, you may need to use an App Password.")
        return
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(content, 'plain'))
        
        # Send email
        logger.info(f"Sending email to {recipient}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {recipient}")
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        logger.warning("Results have been saved to file, but email failed.")


def main():
    """Main execution function."""
    # Setup logging first
    logger = setup_logging(LOG_DIR)
    
    logger.info("=" * 60)
    logger.info("AI News Research Script")
    logger.info("=" * 60)
    
    # Load prompt
    prompt = load_prompt(PROMPT_FILE, logger)
    
    # Initialize OpenAI client
    client = get_openai_client(logger)
    
    # Call OpenAI API
    results = call_openai(client, prompt, logger)
    
    # Save results
    filepath = save_results(results, OUTPUT_DIR, logger)
    
    # Send email (if recipient is configured)
    if EMAIL_RECIPIENT:
        send_email(results, EMAIL_RECIPIENT, logger)
    else:
        logger.warning("EMAIL_RECIPIENT not set in .env file. Skipping email.")
    
    logger.info("=" * 60)
    logger.info("Script completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
