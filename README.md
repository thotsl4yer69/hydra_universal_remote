# hydra_universal_remote

![CI](https://github.com/thotsl4yer69/maz-ai-orchestrator/actions/workflows/ci-clean.yml/badge.svg)

Minimal runner and instructions for local development.

Prereqs

- Python 3.8+ (recommended 3.10/3.11 for hardware packages). Create and activate a virtualenv.

Install dependencies

```powershell
python -m pip install -r requirements.txt
```

Install developer/test dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

Run a smoke-run

```powershell
python -m src.main
```

Run tests

```powershell
python -m unittest discover -v
```

Notes

- This project integrates with BLE devices (via `bleak`) and Flipper Zero protobufs
  (`flipperzero-protobuf-py`). Hardware-specific code is intentionally absent from
  the smoke-run and tests — add hardware logic under `src/device/` and mock it in tests.

CI

- The repository includes a GitHub Actions workflow that runs unit tests on Python 3.10 and 3.11, and an optional manual integration job that runs on 3.11 to exercise hardware-adjacent steps.
