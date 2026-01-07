"""
Pushover notification utilities for AI Research Script
"""

import os
import requests
import logging


def send_pushover_notification(success: bool, job_name: str, message: str, logger: logging.Logger):
    """Send Pushover notification with success/failure status."""
    pushover_user_key = os.getenv("PUSHOVER_USER_KEY")
    pushover_app_token = os.getenv("PUSHOVER_APP_TOKEN")
    
    if not pushover_user_key or not pushover_app_token:
        logger.warning("Pushover credentials not configured.")
        logger.warning("Set PUSHOVER_USER_KEY and PUSHOVER_APP_TOKEN in .env file to enable notifications.")
        return
    
    try:
        # Determine priority and sound based on success/failure
        if success:
            priority = 0  # Normal priority
            title = f"✅ {job_name} - Success"
            sound = "pushover"  # Default sound
        else:
            priority = 1  # High priority (requires acknowledgment)
            title = f"❌ {job_name} - Failed"
            sound = "siren"  # Alert sound for failures
        
        # Prepare the message
        payload = {
            "token": pushover_app_token,
            "user": pushover_user_key,
            "title": title,
            "message": message,
            "priority": priority,
            "sound": sound
        }
        
        logger.info(f"Sending Pushover notification ({'success' if success else 'failure'})...")
        response = requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=10)
        response.raise_for_status()
        
        logger.info("Pushover notification sent successfully")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Pushover notification: {e}", exc_info=True)
        logger.warning("Pushover notification failed, but script execution continues.")
    except Exception as e:
        logger.error(f"Unexpected error sending Pushover notification: {e}", exc_info=True)
        logger.warning("Pushover notification failed, but script execution continues.")
