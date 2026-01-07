# AI News Research Script

This script calls OpenAI's latest agentic chat completion model to generate AI news research based on the prompt in `ai-research-prompt.md`, saves the results to a dated file, and emails them.

## Setup

**Quick Setup (Recommended):**

1. **Install required system packages (one-time, requires sudo):**
   ```bash
   sudo apt install python3-venv python3-pip
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

   This will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Set everything up for you

**Manual Setup (Alternative):**

If you prefer to set up manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. Create a `.env` file for your credentials:
```bash
cp .env.example .env
```

5. Edit the `.env` file and add your credentials:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Email Configuration
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password-here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Important Security Notes:**
- The `.env` file is already in `.gitignore` and will NOT be committed to GitHub
- Never commit your `.env` file or share it with anyone
- For Gmail, you'll need to:
  - Enable 2-factor authentication
  - Generate an App Password: https://myaccount.google.com/apppasswords

## Usage

**If using a virtual environment, activate it first:**
```bash
source venv/bin/activate
```

Run the script:
```bash
python ai_news_research.py
```

The script will:
1. Load the prompt from `ai-research-prompt.md`
2. Call OpenAI's agentic model (o1-preview)
3. Save results to `data/YYYY-MM-DD AI News Research.md`
4. Email the results to christopher.j.obrien@gmail.com

## Output

Results are saved in the `data/` directory with filenames like:
- `2024-01-15 AI News Research.md`
