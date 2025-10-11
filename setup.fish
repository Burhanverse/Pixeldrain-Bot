#!/usr/bin/env fish

# Setup script for Pixeldrain Bot (Fish Shell)
# This script sets up a virtual environment and installs dependencies

echo "Setting up Pixeldrain Bot..."

# Create virtual environment if it doesn't exist
if not test -d "venv"
    echo "Creating virtual environment..."
    python -m venv venv
end

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate.fish

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
