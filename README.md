# Hydra Universal Remote

**BLE/protobuf device-integration experiment with a testable Python core.**

[![Status](https://img.shields.io/badge/status-software%20prototype-blue)](PROJECT_STATUS.md)

> **Maturity: Software prototype.** “Universal remote” is the product direction, not a claim that the repository can control every device. Compatibility should be stated only for hardware/protocol combinations actually tested.

## What it explores

Hydra is a small Python project for experimenting with control layers around BLE-connected hardware and protobuf-based device interfaces.

The repository is intentionally structured so hardware-specific behaviour can sit behind a testable application boundary rather than making every unit test require a physical device.

## Relevant technology

- Python;
- `bleak` for Bluetooth Low Energy integration;
- Flipper/protobuf-related integration libraries where used by the selected revision;
- device adapters under the project source tree;
- mocks/fakes for hardware-independent tests;
- GitHub Actions / Python test automation.

## Setup

Create a virtual environment, then install the runtime and development dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Smoke-run the software-only path:

```bash
python -m src.main
```

Run tests:

```bash
python -m unittest discover -v
```

## Hardware boundary

The smoke run and ordinary unit tests are deliberately hardware-independent. Add or modify real device logic under the relevant device/adaptor layer and mock external hardware in unit tests.

A passing software test does not prove BLE connectivity to a physical target. Hardware integration should record:

- exact device/model/firmware;
- BLE services/characteristics used;
- protocol/protobuf version;
- discovery/pairing requirements;
- tested commands;
- failure/reconnection behaviour.

## Provenance

Third-party protobuf definitions, libraries and device protocols remain attributable to their upstream authors/vendors. The portfolio claim is the local integration/adaptor work, not authorship of those protocols.

## Portfolio significance

**Python · BLE · protobuf · hardware abstraction · testing · device integration**
