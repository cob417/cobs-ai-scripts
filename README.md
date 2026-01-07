# Run AI Script

A generic, modular script runner that executes any OpenAI prompt-based script. Loads prompts from the `prompts/` directory, calls OpenAI's API with web browsing support, and saves/emails the results.

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
python run_ai_script.py
```

Or with a custom prompt:
```bash
python run_ai_script.py -p my-custom-prompt.md
```

The script will:
1. Load the prompt from the `prompts/` directory (default: `ai-research-prompt.md`)
2. Call OpenAI's API with web browsing support (default: gpt-5.2)
3. Save results to `data/YYYY-MM-DD [prompt-name].md`
4. Email the results (if EMAIL_RECIPIENT is configured)

## Output

Results are saved in the `data/` directory with filenames based on the prompt name:
- `2024-01-15 ai-research-prompt.md`
- `2024-01-15 my-custom-prompt.md`
