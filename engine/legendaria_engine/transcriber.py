"""Speech-to-text. A small backend interface keeps room for other engines (e.g. Apple Silicon)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from legendaria_engine.events import Reporter
from legendaria_engine.schema import Segment, Transcript, Word


@dataclass
class Options:
    """Everything a backend needs to run one transcription."""

    model: str
    model_path: Path
    language: str | None  # None = auto-detect
    device: str  # auto | cuda | cpu
    compute_type: dict[str, str]
    beam_size: int = 5
    vad_filter: bool = True
    word_timestamps: bool = True


class Backend(Protocol):
    """Interface for speech-to-text engines (faster-whisper today; Apple Silicon later)."""

    name: str

    def transcribe(self, media: Path, options: Options, reporter: Reporter) -> Transcript:
        """Transcribe `media`, reporting progress, and return the transcript."""
        ...


def cuda_available() -> bool:
    """True when CTranslate2 sees at least one CUDA device."""
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False


class FasterWhisperBackend:
    """faster-whisper (CTranslate2): CUDA on NVIDIA GPUs, int8 on CPU."""

    name = "faster-whisper"

    def _devices(self, options: Options) -> list[str]:
        if options.device != "auto":
            return [options.device]
        return ["cuda", "cpu"] if cuda_available() else ["cpu"]

    def transcribe(self, media: Path, options: Options, reporter: Reporter) -> Transcript:
        """Try each device in turn; in `auto` mode a GPU failure falls back to the CPU.

        CUDA problems (missing libraries, out of memory) can surface when the model loads
        or only once decoding starts, so the whole run is retried.
        """
        devices = self._devices(options)
        for i, device in enumerate(devices):
            try:
                return self._run(media, options, device, reporter)
            except Exception as exc:
                if i == len(devices) - 1:
                    raise RuntimeError(f"Transcription failed on {device}: {exc}") from exc
                reporter.warning(f"GPU unavailable ({exc}); falling back to CPU, which is slower.")
        raise AssertionError("unreachable")

    def _run(self, media: Path, options: Options, device: str, reporter: Reporter) -> Transcript:
        from faster_whisper import WhisperModel

        compute_type = options.compute_type.get(device, "default")
        model = WhisperModel(str(options.model_path), device=device, compute_type=compute_type)
        segments_iter, info = model.transcribe(
            str(media),
            language=options.language,
            beam_size=options.beam_size,
            vad_filter=options.vad_filter,
            word_timestamps=options.word_timestamps,
        )
        reporter.emit(
            "start",
            model=options.model,
            device=device,
            compute_type=compute_type,
            language=info.language,
            language_probability=round(info.language_probability, 4),
            duration=round(info.duration, 2),
        )
        segments = []
        for seg in segments_iter:  # lazy: decoding happens while iterating
            words = [
                Word(
                    start=round(w.start, 3),
                    end=round(w.end, 3),
                    word=w.word,
                    probability=round(w.probability, 4),
                )
                for w in (seg.words or [])
            ]
            segments.append(
                Segment(
                    start=round(seg.start, 3),
                    end=round(seg.end, 3),
                    text=seg.text.strip(),
                    words=words,
                )
            )
            reporter.progress(seg.end, info.duration)
        reporter.progress(info.duration, info.duration)
        return Transcript(
            source=media.name,
            language=info.language,
            language_probability=round(info.language_probability, 4),
            duration=round(info.duration, 2),
            model=options.model,
            device=device,
            segments=segments,
        )


BACKENDS: dict[str, type] = {"faster-whisper": FasterWhisperBackend}


def get_backend(name: str = "faster-whisper") -> Backend:
    """Instantiate a backend by name."""
    if name not in BACKENDS:
        raise KeyError(f"Unknown backend '{name}'. Available: {', '.join(BACKENDS)}")
    return BACKENDS[name]()
