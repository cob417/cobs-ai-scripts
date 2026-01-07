#!/usr/bin/env python3
"""
AI News Research Script
Calls OpenAI's latest agentic chat completion model to generate AI news research
and saves/emails the results.
"""

import os
import sys
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
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

# OpenAI model - can be overridden via OPENAI_MODEL environment variable
# Default to gpt-5.2 with browsing (best for research tasks)
# For reasoning models, use: o1, o1-preview, o3-preview, o3-mini
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.2")

# Enable web browsing for research tasks (can be disabled via WEB_SEARCH env var)
ENABLE_WEB_SEARCH = os.getenv("WEB_SEARCH", "true").lower() == "true"


def load_prompt(prompt_file: Path) -> str:
    """Load the prompt from the markdown file."""
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file '{prompt_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading prompt file: {e}")
        sys.exit(1)


def get_openai_client() -> OpenAI:
    """Initialize and return OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def call_openai(client: OpenAI, prompt: str) -> str:
    """Call OpenAI's Responses API with web browsing if enabled."""
    print(f"Calling OpenAI API with model: {OPENAI_MODEL}...")
    
    try:
        # Use Responses API (same as ChatGPT UI) with web search tool if enabled
        if ENABLE_WEB_SEARCH:
            print("Using Responses API with web browsing enabled...")
            response = client.responses.create(
                model=OPENAI_MODEL,
                input=prompt,
                tools=[{"type": "web_search"}],  # Enable web browsing (same as ChatGPT UI)
                include=["web_search_call.action.sources"],  # Optional: return sources
            )
            print("Web browsing enabled successfully!")
            return response.output_text
        else:
            # Fallback to Chat Completions API if web browsing is disabled
            print("Using Chat Completions API (web browsing disabled)...")
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            return response.choices[0].message.content
    except AttributeError as e:
        # Responses API might not be available in older library versions
        if "responses" in str(e).lower():
            print("Warning: Responses API not available in this OpenAI library version.")
            print("Falling back to Chat Completions API...")
            print("To enable web browsing, update: pip install --upgrade openai")
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
            return response.choices[0].message.content
        else:
            raise
    except Exception as e:
        error_msg = str(e)
        print(f"Error calling OpenAI API: {e}")
        
        # Provide helpful suggestions for common errors
        if "model" in error_msg.lower() and ("not exist" in error_msg.lower() or "not found" in error_msg.lower()):
            print("\nSuggested fixes:")
            print("1. Check if the model name is correct. Available models include:")
            print("   - gpt-5.2 (recommended for research with web browsing)")
            print("   - gpt-4o (widely available, no browsing)")
            print("   - gpt-4-turbo")
            print("   - gpt-4")
            print("2. Set OPENAI_MODEL in your .env file, e.g.:")
            print("   OPENAI_MODEL=gpt-5.2")
            print("3. To enable web browsing:")
            print("   - Update OpenAI library: pip install --upgrade openai")
            print("   - Ensure your account has Responses API access")
            print("   - Set WEB_SEARCH=true in .env (default)")
        elif "responses" in error_msg.lower():
            print("\nNote: Responses API may require:")
            print("   - Updated OpenAI library: pip install --upgrade openai")
            print("   - Account access to Responses API")
            print("   - Falling back to Chat Completions API without browsing...")
            # Try fallback
            try:
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content
            except Exception as fallback_error:
                print(f"Fallback also failed: {fallback_error}")
                sys.exit(1)
        
        sys.exit(1)


def save_results(content: str, output_dir: Path) -> str:
    """Save results to a dated file in the output directory."""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with current date and time (hours, minutes, seconds)
    ts = datetime.now().strftime("%Y-%m-%d AI News Research %H%M%S")
    filename = f"{ts}.md"
    filepath = output_dir / filename
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Results saved to: {filepath}")
    return str(filepath)


def send_email(content: str, recipient: str, subject: str = None):
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
        print("Warning: Email credentials not configured.")
        print("Set EMAIL_USER and EMAIL_PASSWORD environment variables to enable email.")
        print("For Gmail, you may need to use an App Password.")
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
        print(f"Sending email to {recipient}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        print(f"Email sent successfully to {recipient}")
    except Exception as e:
        print(f"Error sending email: {e}")
        print("Results have been saved to file, but email failed.")


def main():
    """Main execution function."""
    print("=" * 60)
    print("AI News Research Script")
    print("=" * 60)
    
    # Load prompt
    print(f"Loading prompt from {PROMPT_FILE.name}...")
    prompt = load_prompt(PROMPT_FILE)
    
    # Initialize OpenAI client
    client = get_openai_client()
    
    # Call OpenAI API
    results = call_openai(client, prompt)
    
    # Save results
    filepath = save_results(results, OUTPUT_DIR)
    
    # Send email (if recipient is configured)
    if EMAIL_RECIPIENT:
        send_email(results, EMAIL_RECIPIENT)
    else:
        print("Warning: EMAIL_RECIPIENT not set in .env file. Skipping email.")
    
    print("=" * 60)
    print("Script completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
