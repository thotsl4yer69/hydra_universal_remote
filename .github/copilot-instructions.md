<!--
Guidance for AI coding agents working on this repository.
Keep it short, actionable, and specific to this codebase.
-->
# Copilot / AI agent instructions — hydra_universal_remote

Goal: help an AI coding agent be immediately productive in this repository.

## Quick context
- Language: Python. Dependencies live in `requirements.txt` (notable packages: `bleak`, `flipperzero-protobuf-py`, `pyyaml`, `ttkthemes`).
- Layout: `src/` with `config/` and `utils/` folders (currently empty). There is no top-level `README.md` or obvious entrypoint in the repository root.

## Big-picture architecture (what to know)
- This project integrates with external devices/protocols: `bleak` implies BLE device interaction; `flipperzero-protobuf-py` indicates usage of Flipper Zero protobuf message types. Treat BLE and protobuf usage as the main external integration surface.
- Code is organized under `src/`. Expect configuration files under `src/config/` (likely YAML based, since `pyyaml` is a dependency) and shared helpers under `src/utils/`.
- Data flow to look for: device -> BLE transport (`bleak`) -> protobuf serialization/deserialization -> application logic -> optional UI (ttk themes suggests a Tkinter-based UI). Search for async/await patterns when adding features (BLE + networking/IO is asynchronous).

## Where to start (key files & searches)
- Read `requirements.txt` to understand runtime dependencies and required native/environmental capabilities.
- Inspect `src/` for modules. If you add features, place reusable helpers in `src/utils/` and configuration schemas in `src/config/`.
- If you need to find protobuf message usage: search for `flipperzero` or `.proto` references.
- For BLE-specific work: search for `bleak` imports and `async` functions that call device read/write APIs.

## Development workflows (how to run & debug)
- Create and activate a virtual environment (use system Python). Then install deps:
  - pip install -r requirements.txt
- There is no documented entrypoint. Before adding a `main` script, search for any existing runnable module under `src/`. If none exists, create `src/main.py` with an async entry function and a small CLI wrapper.
- Debugging tips:
  - Use an interactive session (REPL) or a small runner script to exercise BLE/protobuf code — these integrations are hardware-dependent.
  - When testing BLE code locally, consider mocking `bleak` calls using `unittest.mock` or an adapter interface.

## Project-specific conventions & patterns
- Configs are likely YAML (dependency `pyyaml`) — treat `src/config/` as the place for YAML schema and loader utilities.
- Use `async`/`await` for IO operations (BLE, network, device I/O). Prefer creating small async functions that are easy to unit test with `pytest` and `asyncio` test support.
- Keep device/protocol code (BLE + protobuf) separated from UI and business logic. If none exists yet, create `src/device/`, `src/proto/`, `src/ui/` as needed to keep boundaries clear.

## Integration points & external dependencies to watch
- BLE: `bleak` — requires platform BLE support and sometimes elevated permissions. Mock during unit tests.
- Flipper Zero protobuf: `flipperzero-protobuf-py` — ensure protobuf message compatibility with any .proto or generated modules.
- YAML configs: `pyyaml` — centralize config loading and validate schema early.

## Examples from this repo
- `requirements.txt` (source of truth for runtime deps):
  - bleak>=0.21.1
  - flipperzero-protobuf-py>=0.17.2
  - pyyaml>=6.0.1

## Small checklist for changes an AI might make
1. Add a small README describing how to run the project (include `pip install -r requirements.txt`).
2. If adding runnable behavior, add `src/main.py` and update docs.
3. Add tests for async device interactions using mocks (place tests under `tests/`).

## When to ask the human
- If you need to run or interact with hardware (BLE/Flipper) — ask for access to test devices, sample protobuf schemas, or example config files.
- If you plan to add or change public APIs or configuration formats, request a brief design confirmation.

---
If anything above is unclear or you want the file to emphasize other conventions (commit messages, branching, CI), tell me what to include and I will iterate.
