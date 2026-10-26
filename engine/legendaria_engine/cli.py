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


def parse_clip(value: str) -> tuple[float, float]:
    """`START,END` in seconds → (start, end); raises ValueError on bad input."""
    try:
        start, end = (float(v) for v in value.split(","))
    except ValueError as exc:
        raise ValueError(f"--clip must be START,END in seconds, got '{value}'") from exc
    if start < 0 or end <= start:
        raise ValueError(f"--clip end must be after start, got '{value}'")
    return start, end


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
    clip = parse_clip(args.clip) if args.clip else None
    if args.update and not clip:
        reporter.error("--update needs --clip (the time range to replace)")
        return 2
    if config["device"] != "cpu":  # make pip-installed CUDA libraries loadable (may re-exec)
        from legendaria_engine.cuda_libs import ensure_cuda_libs

        ensure_cuda_libs()
    from legendaria_engine import models
    from legendaria_engine.transcriber import Options, get_backend

    language = None if config["language"] == "auto" else config["language"]
    glossary = load_glossary(args, media, reporter)
    hotwords = None
    if glossary and config["review"].get("glossary_bias", True):
        from legendaria_engine.review.bias import hotwords as make_hotwords

        hotwords = make_hotwords(glossary)
    options = Options(
        model=config["model"],
        model_path=models.resolve(config["model"], reporter),
        language=language,
        device=config["device"],
        compute_type=config["compute_type"],
        beam_size=config["beam_size"],
        vad_filter=config["vad_filter"],
        word_timestamps=config["word_timestamps"],
        clip=clip,
        hotwords=hotwords,
    )
    transcript = get_backend(config.get("backend", "faster-whisper")).transcribe(
        media, options, reporter
    )
    if args.update:
        base = Transcript.load(Path(args.update).expanduser())
        transcript = base.merged_with(transcript, *clip)
    out_dir = Path(args.output_dir).expanduser() if args.output_dir else media.parent
    stem = out_dir / media.stem
    extra: dict = {}
    if args.review:
        transcript, extra = run_review(
            transcript, glossary, config, stem, reporter, wants_llm(config, None)
        )
    outputs = write_outputs(transcript, stem, config["formats"], config, style)
    reporter.emit(
        "done",
        outputs=outputs + extra.get("outputs", []),
        segments=len(transcript.segments),
        language=transcript.language,
        **{k: v for k, v in extra.items() if k != "outputs"},
    )
    return 0


def load_glossary(args: argparse.Namespace, media: Path, reporter: Reporter):
    """Global + project (next to `media`) + `--glossary` files, unless `--no-glossary`."""
    from legendaria_engine.review import glossary

    if getattr(args, "no_glossary", False):
        return glossary.Glossary()
    merged = glossary.load(getattr(args, "glossary", None) or [], media=media)
    if merged:
        names = ", ".join(str(p) for p in merged.sources)
        reporter.log(f"Glossary: {len(merged.terms)} terms, {len(merged.fixes)} fixes ({names})")
    return merged


def wants_llm(config: dict, flag: bool | None) -> bool | None:
    """True/False when decided by the flag or config; None means "auto" (use it if reachable)."""
    if flag is not None:
        return flag
    review_cfg = config["review"]
    if review_cfg.get("profile", "auto") in ("light", "standard"):
        return False
    if review_cfg.get("profile") == "full":
        return True
    enabled = review_cfg.get("llm", {}).get("enabled", "auto")
    return None if enabled == "auto" else bool(enabled)


def run_review(
    transcript: Transcript,
    glossary,
    config: dict,
    stem: Path,
    reporter: Reporter,
    use_llm: bool | None = False,
    llm_overrides: dict | None = None,
):
    """Glossary fixes (layer 2) and, when wanted, the LLM reviewer (layer 3).

    Writes `<stem>.review.json` in suggest mode, or applies everything in auto mode.
    """
    from legendaria_engine.review import fix_rules
    from legendaria_engine.review.suggestions import Review, apply

    review_cfg = config["review"]
    low = review_cfg.get("low_confidence", 0.5)
    found = fix_rules.suggest(
        transcript, glossary, threshold=review_cfg.get("fuzzy_threshold", 0.82), low_confidence=low
    )
    extra: dict = {}
    if use_llm is not False:
        llm_found, info = run_llm(
            transcript, glossary, review_cfg, reporter, use_llm, llm_overrides or {}
        )
        taken = {(s.segment, i) for s in found for i in range(s.first, s.last)}
        llm_found = [
            s for s in llm_found if not any((s.segment, i) in taken for i in range(s.first, s.last))
        ]
        found = sorted(found + llm_found, key=lambda s: (s.segment, s.first))
        extra.update(info)
    for number, s in enumerate(found, start=1):
        s.id = number
        reporter.emit(
            "suggestion",
            id=s.id,
            start=s.start,
            before=s.before,
            after=s.after,
            source=s.source,
            reason=s.reason,
        )
    if review_cfg.get("mode", "suggest") == "auto":
        for s in found:
            s.status = "accepted"
        return apply(transcript, found), {**extra, "applied": len(found)}
    path = stem.parent / f"{stem.name}.review.json"
    Review(transcript=str(stem.parent / f"{stem.name}.json"), suggestions=found).save(path)
    return transcript, {**extra, "outputs": [str(path)], "suggestions": len(found)}


def run_llm(transcript, glossary, review_cfg: dict, reporter: Reporter, use_llm, overrides: dict):
    """Layer 3 with graceful degradation: in auto mode an unreachable server just skips it."""
    from legendaria_engine.review import llm, reviewer

    llm_cfg = review_cfg.get("llm", {})
    try:
        settings = llm.resolve(llm_cfg, **overrides)
        client = llm.LLMClient(settings)
        client.pick_model()
    except llm.LLMError as exc:
        if use_llm is None:
            reporter.warning(f"LLM reviewer unavailable, using the glossary only ({exc})")
            return [], {"llm": "unavailable"}
        raise
    reporter.log(f"LLM reviewer: {settings.provider} / {settings.model}")
    try:
        found, rejected = reviewer.review(
            transcript,
            client,
            glossary,
            reporter,
            low_confidence=review_cfg.get("low_confidence", 0.5),
            batch_lines=llm_cfg.get("batch_lines", 20),
            context_lines=llm_cfg.get("context_lines", 2),
            max_change_ratio=llm_cfg.get("max_change_ratio", 0.35),
        )
    finally:
        if llm_cfg.get("unload_after", True):
            client.unload()
    if rejected:
        reporter.log(f"LLM changes rejected by the guard (rewrites): {rejected}")
    return found, {"llm": f"{settings.provider}/{settings.model}", "llm_rejected": rejected}


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


def cmd_review(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub review FILE.json` (suggest or auto) and `flosub review apply FILE.review.json`."""
    if args.target[0] == "apply":
        if len(args.target) != 2:
            reporter.error("Usage: flosub review apply FILE.review.json [--ids 1,2 | --all]")
            return 2
        return review_apply(Path(args.target[1]).expanduser(), args, reporter)
    source = Path(args.target[0]).expanduser()
    transcript = Transcript.load(source)
    config = load_config({"review": {"mode": args.mode} if args.mode else {}})
    glossary = load_glossary(args, source, reporter)
    use_llm = wants_llm(config, args.llm)
    if not glossary and use_llm is False:
        reporter.error(
            "No glossary found and the LLM is off. Add terms with `flosub glossary add`, "
            "pass --glossary, or use --llm."
        )
        return 2
    stem = source.parent / source.name.removesuffix(".json")
    overrides = {"provider": args.provider, "model": args.llm_model, "base_url": args.base_url}
    transcript, extra = run_review(transcript, glossary, config, stem, reporter, use_llm, overrides)
    outputs = extra.pop("outputs", [])
    if "applied" in extra:
        transcript.save(source)
        outputs.append(str(source))
    reporter.emit("done", outputs=outputs, **extra)
    return 0


def review_apply(path: Path, args: argparse.Namespace, reporter: Reporter) -> int:
    """Apply accepted suggestions (`--ids`, or every pending one with `--all`) to the transcript."""
    from legendaria_engine.review.suggestions import Review, apply

    review = Review.load(path)
    if args.ids:
        wanted = {int(i) for i in args.ids.split(",") if i.strip()}
    elif args.all:
        wanted = {s.id for s in review.suggestions if s.status == "pending"}
    else:
        reporter.error("Choose suggestions with --ids 1,2 or --all")
        return 2
    chosen = [s for s in review.suggestions if s.id in wanted]
    for s in review.suggestions:
        if s.id in wanted:
            s.status = "accepted"
        elif args.reject_rest and s.status == "pending":
            s.status = "rejected"
    transcript_path = Path(review.transcript)
    transcript = apply(Transcript.load(transcript_path), chosen)
    transcript.save(transcript_path)
    review.save(path)
    outputs = [str(transcript_path), str(path)]
    if args.format:
        config = load_config()
        style = check_style(config, args.style)
        stem = transcript_path.parent / transcript_path.name.removesuffix(".json")
        outputs += write_outputs(
            transcript, stem, [f for f in args.format if f != "json"], config, style
        )
    reporter.emit("done", outputs=outputs, applied=len(chosen))
    return 0


def cmd_llm(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub llm check|providers`: test the reviewer's server and list its models."""
    from legendaria_engine.review import llm

    if args.action == "providers":
        print(json.dumps(llm.load_providers(), ensure_ascii=False, indent=2))
        return 0
    config = load_config()
    result: dict = {"ok": False}
    try:
        settings = llm.resolve(
            config["review"].get("llm", {}),
            provider=args.provider,
            base_url=args.base_url,
            model=args.llm_model,
        )
        result.update(provider=settings.provider, base_url=settings.base_url)
        client = llm.LLMClient(settings)
        result["models"] = client.list_models()
        result["model"] = client.pick_model()
        result["ok"] = True
    except llm.LLMError as exc:
        result["error"] = str(exc)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


def cmd_glossary(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub glossary path|show|add` (global by default, or the project of --media)."""
    from legendaria_engine.review import glossary

    if args.file:
        target = Path(args.file).expanduser()
    elif args.media:
        target = glossary.project_file(Path(args.media).expanduser())
    else:
        target = glossary.global_file()
    if args.action == "path":
        print(target)
    elif args.action == "add":
        if not args.entry:
            reporter.error('Usage: flosub glossary add "Term" or "wrong -> right"')
            return 2
        added = glossary.add_entry(target, args.entry)
        reporter.emit("done", outputs=[str(target)], added=added, entry=args.entry)
    else:
        merged = glossary.load(
            [args.file] if args.file else [], media=Path(args.media) if args.media else None
        )
        print(
            json.dumps(
                {
                    "sources": [str(p) for p in merged.sources],
                    "terms": merged.terms,
                    "fixes": merged.fixes,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
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
    t.add_argument("--clip", help="transcribe only START,END (seconds from the media start)")
    t.add_argument(
        "--update",
        help="with --clip: transcript JSON to update; segments in the range are replaced",
    )
    t.set_defaults(func=cmd_transcribe)

    t.add_argument(
        "--glossary",
        action="append",
        metavar="FILE",
        help="glossary file (repeatable); the global one and legendaria-glossary.txt next to the media are used too",
    )
    t.add_argument("--no-glossary", action="store_true", help="ignore every glossary")
    t.add_argument(
        "--review",
        action="store_true",
        help="after transcribing, suggest (or apply, in auto mode) glossary corrections",
    )

    r = sub.add_parser("review", help="suggest glossary corrections, or apply chosen ones")
    r.add_argument("target", nargs="+", help="FILE.json, or: apply FILE.review.json")
    r.add_argument("--glossary", action="append", metavar="FILE", help="extra glossary file")
    r.add_argument("--no-glossary", action="store_true", help=argparse.SUPPRESS)
    r.add_argument("--mode", choices=["suggest", "auto"], help="default from config (suggest)")
    r.add_argument(
        "--llm", dest="llm", action="store_true", default=None, help="use the LLM reviewer"
    )
    r.add_argument("--no-llm", dest="llm", action="store_false", help="glossary fixes only")
    r.add_argument("--provider", help="LLM provider (see `flosub llm providers`)")
    r.add_argument("--model", dest="llm_model", help="LLM model id")
    r.add_argument("--base-url", help="LLM server URL (OpenAI-compatible)")
    r.add_argument("--ids", help="apply: comma-separated suggestion ids")
    r.add_argument("--all", action="store_true", help="apply: every pending suggestion")
    r.add_argument("--reject-rest", action="store_true", help="apply: mark the others rejected")
    r.add_argument("--format", type=parse_formats, help="apply: also re-export (cues,srt,vtt)")
    r.add_argument("--style", help="apply: cue style for the re-export")
    r.set_defaults(func=cmd_review)

    llm_parser = sub.add_parser("llm", help="check the LLM reviewer's server, list providers")
    llm_parser.add_argument("action", choices=["check", "providers"])
    llm_parser.add_argument("--provider")
    llm_parser.add_argument("--model", dest="llm_model")
    llm_parser.add_argument("--base-url")
    llm_parser.set_defaults(func=cmd_llm)

    g = sub.add_parser("glossary", help="show, locate or add to a glossary")
    g.add_argument("action", choices=["show", "path", "add"])
    g.add_argument("entry", nargs="?", help='add: "Term" or "wrong -> right"')
    g.add_argument("--media", help="use the project glossary next to this media file")
    g.add_argument("--file", help="use this glossary file")
    g.set_defaults(func=cmd_glossary)

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
