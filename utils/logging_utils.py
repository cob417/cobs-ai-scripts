"""
Logging utilities for AI Research Script
"""

import sys
import logging
from datetime import datetime
from pathlib import Path


def setup_logging(log_dir: Path, prompt_name: str) -> logging.Logger:
    """Setup logging to a file with naming convention matching data files."""
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with same convention as data files
    ts = datetime.now().strftime(f"%Y-%m-%d {prompt_name} %H%M%S")
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
