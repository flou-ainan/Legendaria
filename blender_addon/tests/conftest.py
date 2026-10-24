import importlib.util
import sys
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1] / "legendaria"


def load(name):
    """Import an add-on module that does not need bpy, without importing the package."""
    spec = importlib.util.spec_from_file_location(f"legendaria_{name}", ADDON / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
