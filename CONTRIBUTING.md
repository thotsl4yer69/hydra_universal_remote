# Contributing to Hydra Universal Remote

## Development Setup

1. Create and activate a virtual environment:
```powershell
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
# Install runtime dependencies
make install

# Install development dependencies
make install-dev
```

## Running Tests

### Unit Tests
Run the full test suite (excluding hardware integration):
```bash
make test
```

### Hardware Integration Tests
Hardware integration tests require:
1. Bluetooth hardware support
2. Windows Bluetooth services running
3. RUN_HARDWARE_INTEGRATION environment variable set

To run hardware tests:

```powershell
# Windows PowerShell
$env:RUN_HARDWARE_INTEGRATION="true"
python -m unittest tests/test_integration_hardware.py -v

# Linux/macOS
RUN_HARDWARE_INTEGRATION=true python -m unittest tests/test_integration_hardware.py -v
```

### Troubleshooting Hardware Tests

If hardware tests are skipped with "device not ready", check:

1. Windows Bluetooth Service:
   - Open Services (services.msc)
   - Ensure "Bluetooth Support Service" is Running
   - Set startup type to Automatic

2. Bluetooth Hardware:
   - Check Windows Settings -> Bluetooth & devices
   - Ensure Bluetooth is turned On
   - Try toggling Bluetooth Off/On

3. Permissions:
   - Run VS Code as Administrator for BLE access
   - Check Windows Security settings for Bluetooth permissions

## Code Style

Run flake8 to check code style:
```bash
make lint
```

## Pull Request Process

1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass (`make test`)
4. Run style checks (`make lint`)
5. Submit PR with clear description of changes

## Development Tips

- Use mocks in `tests/test_device.py` as examples for testing BLE code
- Check `src/utils/ble.py` for helper functions when working with BLE devices
- Configuration lives in `src/config/config.yaml`