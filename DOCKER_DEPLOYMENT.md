# Docker Deployment Guide

This guide explains how to deploy Cob's AI Scripts using Docker, including deployment to Unraid.

## Prerequisites

- Docker installed on your system
- OpenAI API key
- (Optional) Email credentials for notifications

## Quick Start with Docker Compose

1. **Build the frontend** (if not already built):
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

2. **Copy the frontend build to backend** (if not already done):
   ```bash
   cp -r frontend/build/* backend/static/
   ```

3. **Set environment variables** in a `.env` file:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

4. **Build and run with docker-compose**:
   ```bash
   docker-compose up -d
   ```

5. **Access the application**:
   Open http://localhost:8000 in your browser

## Building the Docker Image

To build the image manually:

```bash
docker build -t cob-ai-scripts:latest .
```

## Running the Container

```bash
docker run -d \
  --name cob-ai-scripts \
  -p 8000:8000 \
  -v $(pwd)/backend/scheduler.db:/app/backend/scheduler.db \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/prompts:/app/prompts \
  -e OPENAI_API_KEY=your-api-key \
  -e EMAIL_USER=your-email@gmail.com \
  -e EMAIL_PASSWORD=your-password \
  cob-ai-scripts:latest
```

## Unraid Deployment

### Option 1: Using Community Applications (Recommended)

1. **Prepare the template**:
   - Copy `unraid-template.xml` to your Unraid server
   - Or add it to Community Applications repository

2. **Install via Docker UI**:
   - Go to Unraid Docker tab
   - Click "Add Container"
   - Select "Cob's AI Scripts" from templates
   - Configure:
     - Port: 8000 (or your preferred port)
     - Volume paths for database, data, and prompts
     - Environment variables (especially OPENAI_API_KEY)

3. **Start the container**

### Option 2: Manual Docker Installation

1. **Build or pull the image**:
   ```bash
   docker build -t cob-ai-scripts:latest .
   # OR if pushed to Docker Hub:
   docker pull your-username/cob-ai-scripts:latest
   ```

2. **Create directories on Unraid**:
   ```bash
   mkdir -p /mnt/user/appdata/cob-ai-scripts/{data,prompts}
   ```

3. **Run the container** via Unraid Docker UI or command line:
   ```bash
   docker run -d \
     --name cob-ai-scripts \
     -p 8000:8000 \
     -v /mnt/user/appdata/cob-ai-scripts/scheduler.db:/app/backend/scheduler.db \
     -v /mnt/user/appdata/cob-ai-scripts/data:/app/data \
     -v /mnt/user/appdata/cob-ai-scripts/prompts:/app/prompts \
     -e OPENAI_API_KEY=your-api-key \
     -e EMAIL_USER=your-email@gmail.com \
     -e EMAIL_PASSWORD=your-password \
     --restart unless-stopped \
     cob-ai-scripts:latest
   ```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_PATH` | Yes | `/app/db/scheduler.db` | Path to SQLite database file |
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-5.2` | OpenAI model to use |
| `WEB_SEARCH` | No | `true` | Enable web search in AI responses |
| `EMAIL_USER` | No | - | Email address for sending notifications |
| `EMAIL_PASSWORD` | No | - | Email password or app password |
| `SMTP_SERVER` | No | `smtp.gmail.com` | SMTP server address |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `PUSHOVER_USER_KEY` | No | - | Pushover user key for notifications |
| `PUSHOVER_APP_TOKEN` | No | - | Pushover application token |

## Volume Mounts

| Name | Container Path | Host Path (Unraid example) |
|------|----------------|---------------------------|
| Database Directory | `/app/db` | `/mnt/user/appdata/cob-ai-scripts/db` |
| Data Directory | `/app/data` | `/mnt/user/appdata/cob-ai-scripts/data` |
| Prompts Directory | `/app/prompts` | `/mnt/user/appdata/cob-ai-scripts/prompts` |

**Important**: Mount the database as a **directory**, not a file. Docker file mounts can be unreliable.

## Updating the Container

1. **Pull/build the new image**:
   ```bash
   docker-compose pull
   # OR
   docker build -t cob-ai-scripts:latest .
   ```

2. **Restart the container**:
   ```bash
   docker-compose up -d
   # OR via Unraid UI: Stop and Start the container
   ```

## Troubleshooting

### Container won't start
- Check logs: `docker logs cob-ai-scripts`
- Verify environment variables are set correctly
- Ensure volume paths exist and are writable

### Database issues
- Ensure the database file path is correct and writable
- Check file permissions on the database file

### Frontend not loading
- Verify `backend/static/` contains the built frontend files
- Rebuild frontend if needed: `cd frontend && npm run build && cp -r build/* ../backend/static/`

### API errors
- Verify `OPENAI_API_KEY` is set correctly
- Check network connectivity from container
- Review container logs for detailed error messages

## Health Check

The container includes a health check that pings `/api/status` every 30 seconds. You can check the health status:

```bash
docker ps  # Shows health status
docker inspect cob-ai-scripts | grep Health
```

## Security Notes

- Never commit `.env` files or API keys to version control
- Use Docker secrets or environment variables for sensitive data
- Consider using Docker secrets in production environments
- The container runs as a non-root user (Python slim image)
