<!--
Guidance for AI coding agents working on this repository.
Keep it short, actionable, and specific to this codebase.
-->
# Copilot / AI agent instructions — hydra_universal_remote

Goal: help an AI coding agent be immediately productive in this repository.

## Quick context
- Python 3.10+ project. Runtime deps live in `requirements.txt`; GUI-only extras in `requirements-gui.txt`; dev tooling in `requirements-dev.txt`.
- Two GUIs coexist: legacy monolith `src/main.py` (still covered by tests) and the newer modular UI under `src/ui/`.
- Config, transports, and signal tooling reside in `src/config/`, `src/device/`, `src/utils/`, and `src/core/`.

## Architecture highlights
- `src/core/runtime.py` hosts `AsyncRuntime`, the background asyncio loop shared by GUI widgets; schedule work with `runtime.run_in_background`.
- `src/core/logging_utils.py` centralises logging setup; call `configure_logging()` before spinning up windows.
- `src/device/device_manager.py` orchestrates `FlipperUSBTransport`, `FlipperBLETransport`, and `MockTransport`, exposing async `scan/connect/test` helpers.
- Tk UI is split into frames (`src/ui/device_frame.py`, `src/ui/signal_browser.py`) composed by `src/ui/main_window.py`.
- Signal assets live in `signals/`; `src/utils/signal_library.py` loads metadata and Sub-GHz payloads from that tree.
- Legacy routines (BLE adapters, notebooks, etc.) remain under `src/main.py` and related device modules—keep backward compatibility unless the migration plan says otherwise.

## Daily workflows
- Install deps: `python -m pip install -r requirements.txt`; add `requirements-dev.txt` when linting/tests are needed.
- Launch new GUI: `python -m src.ui.main_window`; legacy smoke run: `python -m src.main`.
- Tests use `unittest`: `python -m unittest discover -v`. Hardware integration is opt-in with `RUN_HARDWARE_INTEGRATION=true python -m unittest tests.test_integration_hardware`.
- `Makefile` mirrors these commands for POSIX shells; on Windows call the `python -m ...` invocations directly.

## Conventions & patterns
- GUI callbacks must stay synchronous; delegate async device work through `self._runtime.run_in_background(...)` and handle completion via Tk `after` callbacks.
- Always surface transport availability via `DeviceManager.scan_devices()`; use `MockTransport` when hardware libs (`pyserial`, `bleak`) are missing.
- Central config comes from `src/config/config.yaml` through `utils.config.load_config`; avoid hard-coding UI defaults.
- `SignalLibrary` auto-creates category folders and persists metadata—reuse it for any signal CRUD to keep `metadata.json` in sync.
- Optional dependencies should stay gracefully guarded (see `device/flipper_transport.py`), logging clear reasons when unavailable.

## Testing & quality
- Existing tests patch `src.main.HydraRemoteGUI`; extend them or add new suites under `tests/` using the same `unittest` style.
- Skip or guard hardware-dependent tests unless `RUN_HARDWARE_INTEGRATION` is explicitly enabled.
- When adding transports or async helpers, mirror the logging and exception patterns already used in `device_manager` and transports.

## Coordinate with the human when…
- Altering the config schema, existing signal formats, or the legacy `src/main.py` execution path.
- Planning changes that require real Flipper Zero hardware, BLE addresses, or proprietary signal files.
- Introducing new external dependencies or platform-specific setup steps beyond those documented in the README.

---
If anything above needs clarification or misses a workflow, let me know and I’ll iterate.
