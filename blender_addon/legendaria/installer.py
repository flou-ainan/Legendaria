# SPDX-License-Identifier: GPL-3.0-or-later
"""The "Install engine" step: set up flosub for users who never open a terminal (plan 02, 2b).

Everything goes into one folder, `<data dir>/engine/` (uv, Python, venv, caches), so
removing that folder uninstalls it. Steps:
  1. download uv (pinned version, SHA-256 checked) for this OS and CPU
  2. create a venv with a uv-managed Python 3.11
  3. install the engine from PyPI (with the `cuda` extra when an NVIDIA GPU is present)
  4. download the default Whisper model
No bpy here: the add-on polls `Installer.state` from a timer.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import threading
import urllib.request
import zipfile
from pathlib import Path

from .engine_bridge import EXE, managed_engine, user_data_dir

UV_VERSION = "0.13.0"
PYTHON_VERSION = "3.11"
ENGINE_SPEC = "legendaria>=0.1.0.dev1,<0.2"
DEFAULT_MODEL = "small"
UV_URL = "https://github.com/astral-sh/uv/releases/download/{version}/{asset}"


def N_(text: str) -> str:
    """Mark a UI message for translation; the add-on translates it when it shows it."""
    return text


def engine_root() -> Path:
    """The single folder that holds everything the installer creates."""
    return user_data_dir() / "engine"


def uv_asset(system: str | None = None, machine: str | None = None) -> str:
    """Release asset name of uv for an OS / CPU pair (defaults to this machine)."""
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    arch = "aarch64" if machine in {"arm64", "aarch64"} else "x86_64"
    if system == "windows":
        return f"uv-{arch}-pc-windows-msvc.zip"
    if system == "darwin":
        return f"uv-{arch}-apple-darwin.tar.gz"
    return f"uv-{arch}-unknown-linux-gnu.tar.gz"


def has_nvidia_gpu() -> bool:
    """True when `nvidia-smi` lists a GPU (Linux / Windows; never on macOS)."""
    if sys.platform == "darwin" or not shutil.which("nvidia-smi"):
        return False
    try:
        out = subprocess.run(
            ["nvidia-smi", "-L"], capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return out.returncode == 0 and "GPU" in out.stdout


def wants_cuda() -> bool:
    """Install GPU support? `LEGENDARIA_INSTALL_CUDA=0|1` decides, else NVIDIA detection."""
    override = os.environ.get("LEGENDARIA_INSTALL_CUDA")
    if override in {"0", "1"}:
        return override == "1"
    return has_nvidia_gpu()


def extract_uv(archive: bytes, asset: str, target_dir: Path) -> Path:
    """Write the uv executable from a release archive into `target_dir`."""
    name = "uv.exe" if asset.endswith(".zip") else "uv"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / name
    if asset.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            member = next(m for m in zf.namelist() if Path(m).name == name)
            target.write_bytes(zf.read(member))
    else:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tf:
            member = next(m for m in tf.getmembers() if Path(m.name).name == name and m.isfile())
            target.write_bytes(tf.extractfile(member).read())
    target.chmod(0o755)
    return target


def verify_sha256(data: bytes, checksum_file: str) -> None:
    """Raise unless `data` matches the first hex digest in a `.sha256` file."""
    expected = checksum_file.split()[0].strip().lower()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(f"uv download checksum mismatch ({actual} != {expected})")


class Installer:
    """Runs the install steps on a background thread; `state` is safe to read anytime."""

    STEPS = ("uv", "python", "engine", "model")

    def __init__(self, with_cuda: bool | None = None, model: str = DEFAULT_MODEL) -> None:
        self.root = engine_root()
        self.with_cuda = wants_cuda() if with_cuda is None else with_cuda
        self.model = model
        self.state = {
            "step": "",
            "index": 0,
            "progress": 0.0,
            "message": "",
            "params": {},
            "error": "",
            "done": False,
        }
        self._thread: threading.Thread | None = None
        self._process: subprocess.Popen | None = None
        self._cancel = False

    # environment shared by every uv call: keep Python, caches and tools inside root
    def _env(self) -> dict:
        env = dict(os.environ)
        env["UV_PYTHON_INSTALL_DIR"] = str(self.root / "python")
        env["UV_CACHE_DIR"] = str(self.root / "cache")
        env["UV_NO_CONFIG"] = "1"
        env.pop("VIRTUAL_ENV", None)
        return env

    def start(self) -> None:
        """Begin installing in the background."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Stop after the current step (the running command is terminated)."""
        self._cancel = True
        if self._process and self._process.poll() is None:
            self._process.terminate()

    def join(self, timeout: float | None = None) -> None:
        """Wait for the background thread (tests and scripts)."""
        if self._thread:
            self._thread.join(timeout)

    @property
    def running(self) -> bool:
        """True while the background thread is working."""
        return self._thread is not None and self._thread.is_alive()

    def _set(self, step: str, message: str, progress: float | None = None) -> None:
        self.state.update(step=step, index=self.STEPS.index(step) + 1, message=message)
        if progress is not None:
            self.state["progress"] = progress

    def _check_cancel(self) -> None:
        if self._cancel:
            raise RuntimeError(N_("Cancelled."))

    def _call(self, args: list[str]) -> None:
        kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        self._process = subprocess.Popen(
            args,
            env=self._env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            **kwargs,
        )
        output = self._process.communicate()[0]
        if self._process.returncode != 0:
            self._check_cancel()
            tail = "\n".join(output.strip().splitlines()[-6:])
            raise RuntimeError(f"{Path(args[0]).name} {args[1]} failed:\n{tail}")

    def _run(self) -> None:
        try:
            uv = self._install_uv()
            self._check_cancel()
            venv = self.root / "venv"
            self._set("python", N_("Installing Python…"), 0.0)
            self._call([str(uv), "venv", "--python", PYTHON_VERSION, "--allow-existing", str(venv)])
            self._check_cancel()
            spec = (
                ENGINE_SPEC.replace("legendaria", "legendaria[cuda]", 1)
                if self.with_cuda
                else ENGINE_SPEC
            )
            message = (
                N_("Installing the engine with GPU support (large download)…")
                if self.with_cuda
                else N_("Installing the engine…")
            )
            self._set("engine", message, 0.0)
            python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            self._call(
                [
                    str(uv),
                    "pip",
                    "install",
                    "--python",
                    str(python),
                    "--prerelease",
                    "allow",
                    "--upgrade",
                    spec,
                ]
            )
            self._check_cancel()
            # The venv holds complete copies/links of every package; the download cache
            # would only double the disk use (several GB with GPU support).
            shutil.rmtree(self.root / "cache", ignore_errors=True)
            self._download_model()
            self.state.update(done=True, progress=1.0, message=N_("Engine installed."))
        except Exception as exc:
            self.state.update(error=str(exc), done=True)

    def _install_uv(self) -> Path:
        uv_dir = self.root / "uv"
        uv = uv_dir / ("uv.exe" if sys.platform == "win32" else "uv")
        self._set("uv", N_("Downloading uv…"), 0.0)
        if uv.is_file():
            return uv
        asset = uv_asset()
        url = UV_URL.format(version=UV_VERSION, asset=asset)
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
        with urllib.request.urlopen(url + ".sha256", timeout=60) as response:
            verify_sha256(data, response.read().decode())
        return extract_uv(data, asset, uv_dir)

    def _download_model(self) -> None:
        engine = managed_engine()
        self._set("model", N_("Downloading the {model} model…"), 0.0)
        self.state["params"] = {"model": self.model}
        kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        self._process = subprocess.Popen(
            [str(engine), "--progress", "json", "models", "download", self.model],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            **kwargs,
        )
        error = ""
        for line in self._process.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("event") == "model_download" and event.get("total"):
                self.state["progress"] = min(1.0, event.get("downloaded", 0) / event["total"])
            elif event.get("event") == "error":
                error = event.get("message", "")
        if self._process.wait() != 0:
            self._check_cancel()
            raise RuntimeError(error or "Model download failed")


def is_installed() -> bool:
    """True when the managed engine exists."""
    return managed_engine().is_file()


def uninstall() -> None:
    """Delete everything the installer created (models live elsewhere and are kept)."""
    shutil.rmtree(engine_root(), ignore_errors=True)


__all__ = [
    "EXE",
    "Installer",
    "engine_root",
    "has_nvidia_gpu",
    "is_installed",
    "uninstall",
    "uv_asset",
]
