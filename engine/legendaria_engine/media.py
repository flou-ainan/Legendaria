"""FFmpeg: find it, read a video's size, burn subtitles in, cut + burn, render a transparent overlay.

FFmpeg (with libass) is only needed for the styled path (`.ass` burn-in and overlay); plain
transcription does not use it. Subtitle files are passed to the `ass` filter by a bare file
name from a temporary folder, so no path escaping is needed on any OS.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import threading
from array import array
from pathlib import Path
from typing import Any

from legendaria_engine.events import Reporter

EXE = ".exe" if sys.platform == "win32" else ""


class MediaError(RuntimeError):
    """FFmpeg is missing or failed."""


def find_tool(config: dict[str, Any], name: str = "ffmpeg") -> Path:
    """`ffmpeg` or `ffprobe`: next to the config's `ffmpeg` path (file or folder), else PATH."""
    custom = config.get("ffmpeg") or ""
    if custom:
        path = Path(custom).expanduser()
        folder = path if path.is_dir() else path.parent
        candidate = folder / f"{name}{EXE}"
        if candidate.is_file():
            return candidate
    found = shutil.which(name)
    if found:
        return Path(found)
    raise MediaError(
        f"{name} not found. Install FFmpeg (https://ffmpeg.org/download.html) and make sure it "
        'is on PATH, or set "ffmpeg" in the config to its location.'
    )


def probe(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Width, height, fps, duration and has_audio of a media file (width/height are None for audio)."""
    result = subprocess.run(
        [
            str(find_tool(config, "ffprobe")),
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise MediaError(f"ffprobe could not read {path}: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    info: dict[str, Any] = {
        "width": None,
        "height": None,
        "fps": None,
        "duration": float(data.get("format", {}).get("duration") or 0),
        "has_audio": any(s.get("codec_type") == "audio" for s in data.get("streams", [])),
    }
    if video:
        info["width"], info["height"] = int(video["width"]), int(video["height"])
        rotation = abs(int(video.get("tags", {}).get("rotate", 0) or 0))
        for side in video.get("side_data_list", []):
            rotation = abs(int(side.get("rotation", rotation) or 0))
        if rotation in (90, 270):  # phone videos: stored landscape, shown portrait
            info["width"], info["height"] = info["height"], info["width"]
        num, _, den = (video.get("avg_frame_rate") or "0/1").partition("/")
        info["fps"] = float(num) / float(den or 1) if float(den or 1) else None
    return info


def video_size(path: Path, config: dict[str, Any]) -> tuple[int, int] | None:
    """(width, height) of a video, or None for audio, a missing file or no ffprobe."""
    try:
        info = probe(path, config)
    except (MediaError, OSError, ValueError):
        return None
    return (info["width"], info["height"]) if info["width"] else None


def run_ffmpeg(
    config: dict[str, Any], args: list[str], duration: float, reporter: Reporter, cwd: Path
) -> None:
    """Run FFmpeg with `args`, reporting progress from `-progress`; raise MediaError on failure."""
    command = [
        str(find_tool(config)),
        "-hide_banner",
        "-nostats",
        "-progress",
        "pipe:1",
        "-y",
        *args,
    ]
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    errors: list[str] = []

    def read_stderr() -> None:
        for line in process.stderr:
            errors.append(line.rstrip())
            del errors[:-20]

    thread = threading.Thread(target=read_stderr, daemon=True)
    thread.start()
    for line in process.stdout:
        key, _, value = line.strip().partition("=")
        if key == "out_time_us" and value.isdigit() and duration:
            reporter.progress(min(int(value) / 1e6, duration), duration)
    process.wait()
    thread.join(timeout=2)
    if process.returncode != 0:
        raise MediaError("FFmpeg failed: " + " | ".join(errors[-5:]))


def _staged(ass_text: str) -> tuple[Path, str]:
    """Write the subtitles to a temp folder; returns (folder, file name for the filter)."""
    folder = Path(tempfile.mkdtemp(prefix="legendaria-"))
    (folder / "subs.ass").write_text(ass_text, encoding="utf-8")
    return folder, "subs.ass"


def burn(
    config: dict[str, Any], video: Path, ass_text: str, output: Path, reporter: Reporter
) -> Path:
    """Burn the subtitles into a copy of `video` (encoder settings from config `burn`)."""
    video, output = Path(video).resolve(), Path(output).resolve()  # FFmpeg runs in a temp dir
    settings = config.get("burn", {})
    duration = probe(video, config)["duration"]
    folder, name = _staged(ass_text)
    try:
        run_ffmpeg(
            config,
            [
                "-i",
                str(video),
                "-vf",
                f"ass={name}",
                *settings.get("video_args", ["-c:v", "libx264", "-crf", "18", "-preset", "medium"]),
                *settings.get("audio_args", ["-c:a", "copy"]),
                str(output),
            ],
            duration,
            reporter,
            folder,
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    return output


def overlay(
    config: dict[str, Any],
    ass_text: str,
    size: tuple[int, int],
    fps: float,
    duration: float,
    output: Path,
    reporter: Reporter,
) -> Path:
    """Render the subtitles alone on a transparent canvas (QuickTime Animation, argb)."""
    output = Path(output).resolve()  # FFmpeg runs in a temp dir
    folder, name = _staged(ass_text)
    canvas = f"color=c=black@0.0:s={size[0]}x{size[1]}:r={fps:.6g}:d={duration:.3f},format=rgba"
    try:
        run_ffmpeg(
            config,
            [
                "-f",
                "lavfi",
                "-i",
                canvas,
                "-vf",
                f"ass={name}:alpha=1",
                "-c:v",
                "qtrle",
                str(output),
            ],
            duration,
            reporter,
            folder,
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    return output


def cut_graph(keep: list[tuple[float, float]], audio: bool, subs: str | None) -> str:
    """Filter graph: trim each kept range, concat them, then burn `subs` (outputs [vo], [ao])."""
    parts, pairs = [], ""
    for i, (start, end) in enumerate(keep):
        parts.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]")
        pairs += f"[v{i}]"
        if audio:
            parts.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")
            pairs += f"[a{i}]"
    outputs = "[vc][ao]" if audio else "[vc]"
    parts.append(f"{pairs}concat=n={len(keep)}:v=1:a={int(audio)}{outputs}")
    parts.append(f"[vc]ass={subs}[vo]" if subs else "[vc]null[vo]")
    return ";".join(parts)


def render(
    config: dict[str, Any],
    video: Path,
    keep: list[tuple[float, float]],
    ass_text: str | None,
    output: Path,
    reporter: Reporter,
) -> Path:
    """One FFmpeg pass: keep only `keep` (source seconds), burn `ass_text` (output time) if given.

    Audio is re-encoded (AAC by default, config `burn.render_audio_args`) since it is cut.
    """
    if not keep:
        raise MediaError("Nothing to render: every part of the video was cut.")
    video, output = Path(video).resolve(), Path(output).resolve()  # FFmpeg runs in a temp dir
    settings = config.get("burn", {})
    audio = probe(video, config)["has_audio"]
    duration = sum(b - a for a, b in keep)
    folder, name = _staged(ass_text or "")
    maps = ["-map", "[vo]", *(["-map", "[ao]"] if audio else [])]
    try:
        run_ffmpeg(
            config,
            [
                "-i",
                str(video),
                "-filter_complex",
                cut_graph(keep, audio, name if ass_text else None),
                *maps,
                *settings.get("video_args", ["-c:v", "libx264", "-crf", "18", "-preset", "medium"]),
                *(
                    settings.get("render_audio_args", ["-c:a", "aac", "-b:a", "192k"])
                    if audio
                    else []
                ),
                str(output),
            ],
            duration,
            reporter,
            folder,
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    return output


def peaks(config: dict[str, Any], path: Path, per_sec: int = 100, rate: int = 8000) -> list[float]:
    """Waveform peaks: the largest |sample| (0 to 1) in each 1/`per_sec` s, decoded by FFmpeg.

    Streams 8 kHz mono PCM through a pipe, so a long video never sits in memory. Empty when
    the media has no audio.
    """
    step = rate // per_sec
    process = subprocess.Popen(
        [
            str(find_tool(config)),
            "-v",
            "error",
            "-i",
            str(path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(rate),
            "-f",
            "s16le",
            "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    out: list[float] = []
    while chunk := process.stdout.read(step * 2 * 2000):
        samples = array("h")
        samples.frombytes(chunk[: len(chunk) // 2 * 2])
        for i in range(0, len(samples), step):
            window = samples[i : i + step]
            out.append(round(max(max(window), -min(window)) / 32768, 3))
    process.wait()
    return out
