#!/bin/bash
# Setup script for Run AI Script

set -e  # Exit on error

echo "=========================================="
echo "Run AI Script - Setup Script"
echo "=========================================="
echo ""

# Check if python3-venv is installed
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "ERROR: python3-venv is not installed."
    echo ""
    echo "Please run this command first (requires sudo):"
    echo "  sudo apt install python3-venv python3-pip"
    echo ""
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To use the script:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Create your .env file:"
echo "     cp .env.example .env"
echo "     # Then edit .env with your credentials"
echo ""
echo "  3. Run the script:"
echo "     python run_ai_script.py"
echo ""
echo "     Or with a custom prompt:"
echo "     python run_ai_script.py -p my-prompt.md"
echo ""
