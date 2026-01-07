"""
Pydantic schemas for API requests and responses
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class JobCreate(BaseModel):
    name: str
    prompt_content: str
    cron_expression: str
    enabled: bool = True
    email_recipients: Optional[List[str]] = None


class JobUpdate(BaseModel):
    name: Optional[str] = None
    prompt_content: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    email_recipients: Optional[List[str]] = None


class JobResponse(BaseModel):
    id: int
    name: str
    prompt_filename: str
    prompt_content: str
    cron_expression: str
    enabled: bool
    email_recipients: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    is_running: Optional[bool] = False  # Whether job is currently running
    
    class Config:
        from_attributes = True


class JobRunResponse(BaseModel):
    id: int
    job_id: int
    job_name: str
    status: str
    output_content: Optional[str] = None  # Markdown
    html_output_content: Optional[str] = None  # HTML formatted
    log_content: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class CronParseRequest(BaseModel):
    cron_expression: str


class CronParseResponse(BaseModel):
    cron_expression: str
    description: str
    next_runs: list[str]  # List of next 5 run times as strings


class StatusResponse(BaseModel):
    scheduler_running: bool
    active_jobs_count: int
    total_jobs_count: int
