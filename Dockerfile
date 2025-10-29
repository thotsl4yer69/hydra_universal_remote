# Hydra Universal Remote Dockerfile for Pi/Nano/Coral
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    libatlas-base-dev libffi-dev libusb-1.0-0-dev \
    bluetooth bluez libbluetooth-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Create venv and install requirements
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Permissions for serial (USB)
RUN groupadd -r dialout && usermod -a -G dialout root

CMD ["/app/venv/bin/python", "-m", "src.main"]
