#!/bin/bash
# Setup script for Hydra Universal Remote on Raspberry Pi (Linux)

set -e

# Update system
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv libatlas-base-dev libffi-dev libusb-1.0-0-dev

# Optional: Bluetooth and BLE support
sudo apt-get install -y bluetooth bluez libbluetooth-dev

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Permissions for serial (USB)
sudo usermod -a -G dialout $USER

echo "Setup complete. Please reboot for group changes to take effect."
