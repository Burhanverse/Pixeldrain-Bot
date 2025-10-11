#!/bin/bash

echo "Setting up Pixeldrain Bot..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    # Use --upgrade-deps to ensure pip/setuptools/wheel are bootstrapped correctly
    # (helps avoid broken pip in the venv on some systems)
    python -m venv --upgrade-deps venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
# This script is bash-specific. If you're using fish, run: source venv/bin/activate.fish
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Validate pip is working
if ! pip --version >/dev/null 2>&1; then
    echo "\nError: pip inside the virtual environment failed to run."
    echo "Common causes: system-managed Python, missing CA bundles, or broken venv bootstrapping."
    echo "Try recreating the venv or run: python -m venv --upgrade-deps venv"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
