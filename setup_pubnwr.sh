#!/bin/bash
# PubNWR Setup Script
# This script sets up the complete PubNWR environment

# Exit on any error
set -e

echo "Starting PubNWR setup..."

# Create main project directory
PROJECT_DIR=~/projects/pubnwr
echo "Creating project directory at ${PROJECT_DIR}..."
mkdir -p ${PROJECT_DIR}
cd ${PROJECT_DIR}

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Create project structure
echo "Creating project directory structure..."
mkdir -p src/{handlers,models,services,utils}
mkdir -p {config,db,system,tests}

# Create __init__.py files
echo "Creating Python package files..."
touch src/__init__.py
touch src/handlers/__init__.py
touch src/models/__init__.py
touch src/services/__init__.py
touch src/utils/__init__.py
touch tests/__init__.py

# Install required Python packages
echo "Installing Python dependencies..."
pip install pylast pylistenbrainz facebook-sdk atproto watchdog pytz requests urllib3

# Setup system directories and user
echo "Setting up system directories and user..."
sudo mkdir -p /opt/pubnwr
sudo mkdir -p /var/lib/pubnwr
sudo mkdir -p /var/log/pubnwr

# Create system user
echo "Creating system user..."
sudo useradd -r -s /bin/false pubnwr || echo "User already exists"

# Set directory permissions
echo "Setting directory permissions..."
sudo chown -R pubnwr:pubnwr /opt/pubnwr
sudo chown -R pubnwr:pubnwr /var/lib/pubnwr
sudo chown -R pubnwr:pubnwr /var/log/pubnwr

# Copy configuration files
echo "Installing configuration files..."
sudo cp config/pubnwr_MYRIAD.ini /etc/pubnwr_MYRIAD.ini
sudo chmod 644 /etc/pubnwr_MYRIAD.ini

# Initialize database
echo "Initializing database..."
sudo -u pubnwr sqlite3 /var/lib/pubnwr/pubnwr.db < db/schema.sql

# Install systemd service
echo "Installing systemd service..."
sudo cp system/pubnwr.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/pubnwr.service
sudo systemctl daemon-reload

# Development setup
echo "Setting up development environment..."
pip install -e .

# Configure logging
sudo touch /var/log/pubnwr/pubnwr.log
sudo touch /var/log/pubnwr/pubnwr.error.log
sudo chown pubnwr:pubnwr /var/log/pubnwr/pubnwr.log
sudo chown pubnwr:pubnwr /var/log/pubnwr/pubnwr.error.log

# Final steps
echo "Installation complete!"
echo
echo "Next steps:"
echo "1. Edit /etc/pubnwr_MYRIAD.ini with your configuration"
echo "2. Start the service:"
echo "   sudo systemctl enable pubnwr"
echo "   sudo systemctl start pubnwr"
echo
echo "3. Check status with:"
echo "   sudo systemctl status pubnwr"
echo
echo "4. View logs with:"
echo "   sudo journalctl -u pubnwr -f"
echo "   or"
echo "   tail -f /var/log/pubnwr/pubnwr.log"
echo
echo "For development:"
echo "- Source virtual environment: source ${PROJECT_DIR}/venv/bin/activate"
echo "- Run directly: python src/main.py"
echo
echo "Setup complete! Remember to configure your social media credentials in the config file."

# Optional: Start service automatically
read -p "Would you like to start the PubNWR service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Starting PubNWR service..."
    sudo systemctl enable pubnwr
    sudo systemctl start pubnwr
    echo "Service started. Check status with: sudo systemctl status pubnwr"
fi

