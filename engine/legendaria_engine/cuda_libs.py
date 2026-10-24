"""Make the NVIDIA libraries installed by pip (cuBLAS, cuDNN) visible to CTranslate2.

The `nvidia-*-cu12` wheels put their shared libraries inside site-packages, where the
dynamic loader does not look. Without this, GPU transcription aborts with
"Unable to load libcudnn_ops.so.9".
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_REEXEC_FLAG = "LEGENDARIA_CUDA_LIBS_SET"


def nvidia_lib_dirs() -> list[Path]:
    """Library folders of the installed `nvidia.*` packages (empty when not installed)."""
    spec = importlib.util.find_spec("nvidia")
    if spec is None or not spec.submodule_search_locations:
        return []
    sub = "bin" if sys.platform == "win32" else "lib"
    dirs = []
    for root in spec.submodule_search_locations:
        for pkg in ("cublas", "cudnn"):
            candidate = Path(root) / pkg / sub
            if candidate.is_dir():
                dirs.append(candidate)
    return dirs


def ensure_cuda_libs() -> None:
    """Expose the NVIDIA libraries to the current process. Call before importing ctranslate2.

    - Linux: `LD_LIBRARY_PATH` is only read at process start, so the process re-executes
      itself once with the folders added.
    - Windows: register the DLL folders and prepend them to PATH.
    - macOS / no NVIDIA packages: nothing to do.
    """
    dirs = nvidia_lib_dirs()
    if not dirs:
        return
    if sys.platform == "win32":
        for d in dirs:
            os.add_dll_directory(str(d))
        os.environ["PATH"] = os.pathsep.join([*map(str, dirs), os.environ.get("PATH", "")])
    elif sys.platform.startswith("linux"):
        current = os.environ.get("LD_LIBRARY_PATH", "")
        missing = [str(d) for d in dirs if str(d) not in current.split(os.pathsep)]
        if missing and not os.environ.get(_REEXEC_FLAG):
            os.environ["LD_LIBRARY_PATH"] = os.pathsep.join(
                [*missing, current] if current else missing
            )
            os.environ[_REEXEC_FLAG] = "1"
            os.execv(sys.executable, [sys.executable, "-m", "legendaria_engine", *sys.argv[1:]])
