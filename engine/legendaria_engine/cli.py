"""`flosub` command line: transcribe, export, models, config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from legendaria_engine import __version__, paths
from legendaria_engine.config import ConfigError, load_config
from legendaria_engine.cues import make_cues
from legendaria_engine.events import Reporter, make_reporter
from legendaria_engine.formats import FORMATS, WRITERS
from legendaria_engine.schema import Transcript


def output_path(stem: Path, fmt: str) -> Path:
    """`<stem>.<fmt>`, or `<stem>.cues.json`; dots in the stem are kept (`a.b.mp4` → `a.b.srt`)."""
    suffix = "cues.json" if fmt == "cues" else fmt
    return stem.parent / f"{stem.name}.{suffix}"


def write_outputs(
    transcript: Transcript, stem: Path, formats: list[str], config: dict, style: str
) -> list[str]:
    """Write the requested formats next to `stem` (no extension); returns the paths.

    `json` is the full transcript; `cues`, `srt` and `vtt` use the cues of `style`.
    """
    stem.parent.mkdir(parents=True, exist_ok=True)
    rules = config["styles"][style]
    cues = make_cues(transcript, rules, style) if set(formats) - {"json"} else None
    written = []
    for fmt in formats:
        target = output_path(stem, fmt)
        if fmt == "json":
            transcript.save(target)
        elif fmt == "cues":
            cues.save(target)
        else:
            target.write_text(WRITERS[fmt](cues, rules.get("line_length")), encoding="utf-8")
        written.append(str(target))
    return written


def check_style(config: dict, style: str | None) -> str:
    """The style to use: `--style` if given, else the config default; must exist."""
    style = style or config["style"]
    if style not in config["styles"]:
        raise ConfigError(f"Unknown style '{style}'. Available: {', '.join(config['styles'])}")
    return style


def parse_formats(value: str | None) -> list[str] | None:
    """argparse type: comma-separated format list, validated against FORMATS."""
    if value is None:
        return None
    formats = [f.strip().lower() for f in value.split(",") if f.strip()]
    unknown = [f for f in formats if f not in FORMATS]
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown format(s): {', '.join(unknown)}")
    return formats


def cmd_transcribe(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub transcribe`: resolve config and model, transcribe, write the outputs."""
    media = Path(args.file).expanduser().resolve()
    if not media.is_file():
        reporter.error(f"File not found: {media}")
        return 2
    config = load_config(
        {
            "model": args.model,
            "language": args.language,
            "device": args.device,
            "formats": args.format,
        }
    )
    style = check_style(config, args.style)
    if config["device"] != "cpu":  # make pip-installed CUDA libraries loadable (may re-exec)
        from legendaria_engine.cuda_libs import ensure_cuda_libs

        ensure_cuda_libs()
    from legendaria_engine import models
    from legendaria_engine.transcriber import Options, get_backend

    language = None if config["language"] == "auto" else config["language"]
    options = Options(
        model=config["model"],
        model_path=models.resolve(config["model"], reporter),
        language=language,
        device=config["device"],
        compute_type=config["compute_type"],
        beam_size=config["beam_size"],
        vad_filter=config["vad_filter"],
        word_timestamps=config["word_timestamps"],
    )
    transcript = get_backend(config.get("backend", "faster-whisper")).transcribe(
        media, options, reporter
    )
    out_dir = Path(args.output_dir).expanduser() if args.output_dir else media.parent
    outputs = write_outputs(transcript, out_dir / media.stem, config["formats"], config, style)
    reporter.emit(
        "done", outputs=outputs, segments=len(transcript.segments), language=transcript.language
    )
    return 0


def cmd_export(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub export`: turn a transcript JSON into cues / SRT / VTT in a given style."""
    source = Path(args.file).expanduser()
    transcript = Transcript.load(source)
    config = load_config()
    style = check_style(config, args.style)
    default_stem = source.parent / source.name.removesuffix(".json")
    stem = Path(args.output) if args.output else default_stem
    outputs = write_outputs(transcript, stem, args.format, config, style)
    reporter.emit("done", outputs=outputs, segments=len(transcript.segments), style=style)
    return 0


def cmd_models(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub models list|download`."""
    from legendaria_engine import models

    if args.action == "download":
        path = models.download(args.name, reporter)
        reporter.emit("done", outputs=[str(path)])
        return 0
    entries = models.list_models()
    if args.json:
        print(
            json.dumps(
                {"models_dir": str(paths.models_dir()), "models": entries}, ensure_ascii=False
            )
        )
    else:
        default = load_config()["model"]
        for m in entries:
            mark = "✓" if m["installed"] else " "
            star = " (default)" if m["name"] == default else ""
            print(
                f"[{mark}] {m['name']:<16} {m.get('size_mb', '?'):>5} MB  {m.get('notes', '')}{star}"
            )
        print(f"\nModels folder: {paths.models_dir()}")
    return 0


def cmd_config(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub config show|path`."""
    if args.action == "path":
        print(paths.user_config_file())
    else:
        print(json.dumps(load_config(), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """The argparse tree for all subcommands."""
    parser = argparse.ArgumentParser(
        prog="flosub", description="Legendária: local automatic subtitles."
    )
    parser.add_argument("--version", action="version", version=f"flosub {__version__}")
    parser.add_argument(
        "--progress",
        choices=["auto", "json", "human"],
        default="auto",
        help="progress output: JSON lines (for programs) or human-readable (default: human in a terminal)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    t = sub.add_parser("transcribe", help="transcribe an audio or video file")
    t.add_argument("file")
    t.add_argument("--model", help="model name (see `flosub models list`) or a model folder")
    t.add_argument("--language", help="language code (pt, en, ...) or 'auto'")
    t.add_argument("--device", choices=["auto", "cuda", "cpu"])
    t.add_argument("--format", type=parse_formats, help="comma-separated: json,cues,srt,vtt")
    t.add_argument(
        "--style", help="cue style: subtitles (default), captions, or one from your config"
    )
    t.add_argument("--output-dir", help="where to write the files (default: next to the input)")
    t.set_defaults(func=cmd_transcribe)

    e = sub.add_parser("export", help="turn a transcript JSON into cues/SRT/VTT")
    e.add_argument("file")
    e.add_argument(
        "--format", type=parse_formats, default=["srt"], help="comma-separated: cues,srt,vtt"
    )
    e.add_argument("--style", help="cue style: subtitles (default), captions, or your own")
    e.add_argument("--output", help="output path without extension (default: next to the JSON)")
    e.set_defaults(func=cmd_export)

    m = sub.add_parser("models", help="list or download Whisper models")
    m_sub = m.add_subparsers(dest="action", required=True)
    m_list = m_sub.add_parser("list")
    m_list.add_argument("--json", action="store_true", help="machine-readable output")
    m_dl = m_sub.add_parser("download")
    m_dl.add_argument("name")
    m.set_defaults(func=cmd_models)

    c = sub.add_parser("config", help="show the merged config or the user config path")
    c.add_argument("action", choices=["show", "path"])
    c.set_defaults(func=cmd_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: run a subcommand and turn every failure into an `error` event."""
    args = build_parser().parse_args(argv)
    reporter = make_reporter(args.progress)
    try:
        return args.func(args, reporter)
    except (ConfigError, KeyError, ValueError, RuntimeError, OSError) as exc:
        reporter.error(str(exc).strip("'\""))
        return 1
    except KeyboardInterrupt:
        reporter.error("Cancelled.")
        return 130
    except Exception as exc:  # unexpected: still report it as an event the add-on can show
        reporter.error(f"{type(exc).__name__}: {exc}")
        return 1
    finally:
        reporter.close()


if __name__ == "__main__":
    sys.exit(main())
