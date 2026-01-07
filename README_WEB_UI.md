# Web UI for AI Script Scheduler

This is a web-based interface for managing scheduled AI script executions.

## Architecture

- **Backend**: FastAPI (Python) with SQLite database
- **Frontend**: React + TypeScript
- **Scheduler**: APScheduler for cron-based job execution

## Setup

### Backend Setup

1. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Start the FastAPI server:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. Install frontend dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## Features

- **Job Management**: Create, edit, delete, and enable/disable scheduled jobs
- **Cron Scheduling**: Visual cron expression builder with live preview (crontab.guru style)
- **Prompt Management**: Manage prompts through the UI (saved as markdown files in `/prompts`)
- **Job History**: View recent job runs with output and logs
- **Manual Execution**: Trigger jobs manually from the UI

## Usage

1. Create a new job by clicking "Create New Job"
2. Enter a job name (used for identification)
3. Enter your prompt content in Markdown format
4. Set the cron schedule (use the visual builder or enter manually)
5. Enable/disable the job as needed
6. View job execution history in the table at the bottom
7. Click "View Details" on any run to see output and logs

## Database

The SQLite database is stored at `backend/scheduler.db` and contains:
- `jobs` table: Scheduled job configurations
- `job_runs` table: Execution history with output and logs

## API Endpoints

- `GET /api/jobs` - List all jobs
- `POST /api/jobs` - Create new job
- `GET /api/jobs/{id}` - Get job details
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job
- `POST /api/jobs/{id}/run` - Manually trigger job
- `POST /api/cron/parse` - Parse cron expression
- `GET /api/job-runs` - List recent runs
- `GET /api/job-runs/{id}` - Get run details
- `GET /api/status` - Get scheduler status
