import hashlib
import io
import tarfile
import zipfile

import pytest
from conftest import load

installer = load("installer")
bridge = load("engine_bridge")


@pytest.mark.parametrize(
    ("system", "machine", "asset"),
    [
        ("Linux", "x86_64", "uv-x86_64-unknown-linux-gnu.tar.gz"),
        ("Linux", "aarch64", "uv-aarch64-unknown-linux-gnu.tar.gz"),
        ("Darwin", "arm64", "uv-aarch64-apple-darwin.tar.gz"),
        ("Darwin", "x86_64", "uv-x86_64-apple-darwin.tar.gz"),
        ("Windows", "AMD64", "uv-x86_64-pc-windows-msvc.zip"),
        ("Windows", "ARM64", "uv-aarch64-pc-windows-msvc.zip"),
    ],
)
def test_uv_asset_names(system, machine, asset):
    assert installer.uv_asset(system, machine) == asset


def test_checksum():
    data = b"uv binary"
    good = hashlib.sha256(data).hexdigest() + "  uv-x86_64-unknown-linux-gnu.tar.gz\n"
    installer.verify_sha256(data, good)
    with pytest.raises(RuntimeError, match="checksum"):
        installer.verify_sha256(b"tampered", good)


def _tar(name, content):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(f"uv-x86_64-unknown-linux-gnu/{name}")
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def _zip(name, content):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, content)
    return buf.getvalue()


def test_extract_from_tar_and_zip(tmp_path):
    uv = installer.extract_uv(
        _tar("uv", b"ELF"), "uv-x86_64-unknown-linux-gnu.tar.gz", tmp_path / "a"
    )
    assert uv.name == "uv" and uv.read_bytes() == b"ELF"
    exe = installer.extract_uv(
        _zip("uv.exe", b"MZ"), "uv-x86_64-pc-windows-msvc.zip", tmp_path / "b"
    )
    assert exe.name == "uv.exe" and exe.read_bytes() == b"MZ"


def test_no_gpu_without_nvidia_smi(monkeypatch):
    monkeypatch.setattr(installer.shutil, "which", lambda name: None)
    assert installer.has_nvidia_gpu() is False


def test_cuda_override(monkeypatch):
    monkeypatch.setattr(installer, "has_nvidia_gpu", lambda: True)
    monkeypatch.setenv("LEGENDARIA_INSTALL_CUDA", "0")
    assert installer.wants_cuda() is False
    assert installer.Installer().with_cuda is False
    monkeypatch.delenv("LEGENDARIA_INSTALL_CUDA")
    assert installer.wants_cuda() is True


def test_everything_lives_in_one_folder():
    assert installer.engine_root() == bridge.user_data_dir() / "engine"
    assert bridge.managed_engine().is_relative_to(installer.engine_root())


def test_engine_spec_allows_patch_updates_only():
    assert installer.ENGINE_SPEC.startswith("legendaria>=") and "<0.2" in installer.ENGINE_SPEC


@pytest.mark.parametrize(
    ("older", "newer"),
    [
        ("flosub 0.1.0.dev0", "0.1.0.dev1"),
        ("0.1.0.dev9", "0.1.0"),
        ("0.1.0", "0.1.1"),
        ("0.9.0", "0.10.0"),
        ("flosub 0.1.0.dev1", "flosub 0.2.0.dev0"),
    ],
)
def test_version_order(older, newer):
    assert bridge.version_key(older) < bridge.version_key(newer)
