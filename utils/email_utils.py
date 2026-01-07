"""
Email utilities for AI Research Script
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(content: str, recipient: str, prompt_name: str, logger: logging.Logger, subject: str = None):
    """Send email with the research results."""
    if subject is None:
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"{prompt_name} - {today}"
    
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
