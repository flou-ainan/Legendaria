import importlib
import sys
import types
from pathlib import Path

ADDON = Path(__file__).resolve().parents[1] / "legendaria"

# Make `legendaria` importable as a package without running its __init__ (which needs bpy),
# so modules that use relative imports (e.g. installer → engine_bridge) load in plain Python.
if "legendaria" not in sys.modules:
    package = types.ModuleType("legendaria")
    package.__path__ = [str(ADDON)]
    sys.modules["legendaria"] = package


def load(name):
    """Import an add-on module that does not need bpy."""
    return importlib.import_module(f"legendaria.{name}")
