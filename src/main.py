import asyncio
from pathlib import Path

# Optional integrations are detected at runtime — keep imports guarded so the
# project can be tested without hardware or native deps installed.
try:
    import bleak  # type: ignore
    _HAS_BLEAK = True
except Exception:
    _HAS_BLEAK = False

try:
    # package name may vary; this is a best-effort detection for the
    # flipper/protobuf package referenced in requirements.txt
    import flipperzero  # type: ignore
    _HAS_FLIPPER = True
except Exception:
    _HAS_FLIPPER = False

def load_config(path: str = None):
    """Load YAML config from `src/config` if present.

    Returns an empty dict on any error to keep the smoke-run simple.
    """
    try:
        import yaml  # imported lazily so module import works without pyyaml installed
    except Exception:
        return {}
    if path is None:
        path = str(Path(__file__).resolve().parents[1] / "config" / "config.yaml")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


async def run_smoke():
    print("hydra_universal_remote smoke-run")
    print(f"bleak available: {_HAS_BLEAK}")
    print(f"flipperzero protobuf available: {_HAS_FLIPPER}")
    cfg = load_config()
    if isinstance(cfg, dict):
        print(f"loaded config keys: {list(cfg.keys())}")
    else:
        print("loaded config (non-dict)")
    print("smoke-run complete — no hardware accessed")


def main():
    asyncio.run(run_smoke())


if __name__ == "__main__":
    main()
