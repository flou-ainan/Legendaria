"""`flosub` command line: transcribe, export, review, glossary, burn, overlay, models, config."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from legendaria_engine import __version__, paths
from legendaria_engine.config import ConfigError, load_config
from legendaria_engine.cues import CueList, make_cues
from legendaria_engine.events import Reporter, make_reporter
from legendaria_engine.formats import FORMATS, WRITERS
from legendaria_engine.schema import Transcript


def output_path(stem: Path, fmt: str) -> Path:
    """`<stem>.<fmt>`, or `<stem>.cues.json`; dots in the stem are kept (`a.b.mp4` → `a.b.srt`)."""
    suffix = "cues.json" if fmt == "cues" else fmt
    return stem.parent / f"{stem.name}.{suffix}"


def write_outputs(
    transcript: Transcript | None,
    stem: Path,
    formats: list[str],
    config: dict,
    style: str,
    size: tuple[int, int] | None = None,
    cues: CueList | None = None,
) -> list[str]:
    """Write the requested formats next to `stem` (no extension); returns the paths.

    `json` is the full transcript; the others use the cues of `style`, or `cues` when
    given (an edited cue list, e.g. from Blender). `ass` is drawn on a `size` canvas.
    """
    from legendaria_engine.ass import to_ass

    stem.parent.mkdir(parents=True, exist_ok=True)
    rules = config["styles"][style]
    if cues is None and set(formats) - {"json"}:
        cues = make_cues(transcript, rules, style)
    written = []
    for fmt in formats:
        target = output_path(stem, fmt)
        if fmt == "json":
            if transcript is None:
                raise ValueError("A cues file has no transcript to write as json")
            transcript.save(target)
        elif fmt == "cues":
            cues.save(target)
        elif fmt == "ass":
            text = to_ass(cues, rules.get("ass"), size, rules.get("line_length"))
            target.write_text(text, encoding="utf-8")
        else:
            target.write_text(WRITERS[fmt](cues, rules.get("line_length")), encoding="utf-8")
        written.append(str(target))
    return written


def parse_size(value: str) -> tuple[int, int]:
    """argparse type: `WIDTHxHEIGHT` → (width, height)."""
    width, _, height = value.lower().partition("x")
    try:
        size = int(width), int(height)
    except ValueError:
        raise argparse.ArgumentTypeError("size must look like 1920x1080") from None
    if min(size) <= 0:
        raise argparse.ArgumentTypeError("size must be positive")
    return size


def canvas_size(
    config: dict, given: tuple[int, int] | None, media: str | Path | None
) -> tuple[int, int] | None:
    """Canvas for `.ass`: `--size`, else the media's video size, else None (1920x1080)."""
    if given:
        return given
    if media and Path(media).is_file():
        from legendaria_engine.media import video_size

        return video_size(Path(media), config)
    return None


def load_subtitles(path: Path) -> tuple[Transcript | None, CueList | None, str | None]:
    """A subtitle source: (transcript, cues, ass text); exactly one is set."""
    if path.suffix.lower() == ".ass":
        return None, None, path.read_text(encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "cues" in data:
        return None, CueList.from_dict(data), None
    return Transcript.from_dict(data), None, None


def ass_for(path: Path, config: dict, style: str, size: tuple[int, int] | None) -> tuple[str, str]:
    """(.ass text, source media) from a transcript, a cues JSON or an `.ass` file."""
    from legendaria_engine.ass import to_ass

    transcript, cues, text = load_subtitles(path)
    if text is not None:
        return text, ""
    rules = config["styles"][style]
    source = transcript.source if transcript else cues.source
    if cues is None:
        cues = make_cues(transcript, rules, style)
    return to_ass(cues, rules.get("ass"), size, rules.get("line_length")), source


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
    size = canvas_size(config, None, media) if "ass" in config["formats"] else None
    outputs = write_outputs(transcript, stem, config["formats"], config, style, size)
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
    """`flosub export`: a transcript (or an edited cues JSON) → cues / SRT / VTT / ASS."""
    source = Path(args.file).expanduser()
    transcript, cues, _ = load_subtitles(source)
    config = load_config()
    style = check_style(config, args.style or (cues.style if cues else None))
    name = source.name.removesuffix(".json").removesuffix(".cues")
    stem = Path(args.output) if args.output else source.parent / name
    media = transcript.source if transcript else cues.source
    size = canvas_size(config, args.size, media) if "ass" in args.format else None
    outputs = write_outputs(transcript, stem, args.format, config, style, size, cues)
    count = len(transcript.segments) if transcript else len(cues.cues)
    reporter.emit("done", outputs=outputs, segments=count, style=style)
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
        formats = [f for f in args.format if f != "json"]
        size = canvas_size(config, None, transcript.source) if "ass" in formats else None
        outputs += write_outputs(transcript, stem, formats, config, style, size)
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
    """`flosub glossary list|new|use|import|export|delete|show|path|add` (the glossary library)."""
    from legendaria_engine.config import update_user_config
    from legendaria_engine.review import glossary

    action, values = args.action, args.values
    if action == "list":
        active = glossary.active_name()
        items = []
        for name in glossary.list_names():
            merged = glossary.Glossary()
            merged.merge_text(glossary.library_file(name).read_text(encoding="utf-8"))
            items.append(
                {
                    "name": name,
                    "active": name == active,
                    "terms": len(merged.terms),
                    "fixes": len(merged.fixes),
                    "path": str(glossary.library_file(name)),
                }
            )
        print(
            json.dumps(
                {"active": active, "folder": str(glossary.library_dir()), "glossaries": items},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if action in ("new", "use", "delete", "export") and not values:
        reporter.error(
            f"Usage: flosub glossary {action} NAME" + (" --to FILE" if action == "export" else "")
        )
        return 2
    if action == "new":
        path = glossary.create(values[0])
        if args.activate:
            update_user_config({"review": {"glossary": values[0]}})
        reporter.emit("done", outputs=[str(path)], name=values[0])
    elif action == "use":
        if values[0] not in glossary.list_names():
            glossary.create(values[0])
        update_user_config({"review": {"glossary": values[0]}})
        reporter.emit("done", outputs=[str(glossary.library_file(values[0]))], active=values[0])
    elif action == "delete":
        glossary.delete(values[0])
        reporter.emit("done", outputs=[], deleted=values[0])
    elif action == "export":
        if not args.to:
            reporter.error("Usage: flosub glossary export NAME --to FILE")
            return 2
        path = glossary.export_file(values[0], Path(args.to))
        reporter.emit("done", outputs=[str(path)], name=values[0])
    elif action == "import":
        if not values:
            reporter.error("Usage: flosub glossary import FILE [--name NAME]")
            return 2
        path = glossary.import_file(Path(values[0]), args.name, overwrite=args.overwrite)
        reporter.emit("done", outputs=[str(path)], name=path.stem)
    elif action == "path":
        print(glossary.library_file(values[0]) if values else glossary.global_file())
    elif action == "add":
        if not values:
            reporter.error(
                'Usage: flosub glossary add "Term" or "wrong -> right" [--name N | --media M | --file F]'
            )
            return 2
        target = glossary_target(args)
        added = glossary.add_entry(target, values[0])
        reporter.emit("done", outputs=[str(target)], added=added, entry=values[0])
    else:  # show
        if values:
            merged = glossary.load([values[0]], use_global=False)
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


def glossary_target(args: argparse.Namespace) -> Path:
    """Where `glossary add` writes: --file, the project of --media, --name, or the active one."""
    from legendaria_engine.review import glossary

    if args.file:
        return Path(args.file).expanduser()
    if args.media:
        return glossary.project_file(Path(args.media).expanduser())
    if args.name:
        return glossary.library_file(args.name)
    return glossary.global_file()


def cmd_burn(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub burn VIDEO`: a copy of the video with the subtitles drawn in (FFmpeg + libass)."""
    from legendaria_engine import media

    video = Path(args.file).expanduser().resolve()
    if not video.is_file():
        reporter.error(f"File not found: {video}")
        return 2
    subs = Path(args.subs).expanduser() if args.subs else video.parent / f"{video.stem}.json"
    if not subs.is_file():
        reporter.error(
            f"Subtitles not found: {subs}. Transcribe first (`flosub transcribe`) or pass --subs."
        )
        return 2
    config = load_config()
    style = check_style(config, args.style)
    text, _ = ass_for(subs, config, style, canvas_size(config, None, video))
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else video.parent / f"{video.stem}.subtitled.mp4"
    )
    if output.resolve() == video:
        reporter.error("The output would overwrite the input video; choose another --output.")
        return 2
    media.burn(config, video, text, output, reporter)
    reporter.emit("done", outputs=[str(output)], style=style)
    return 0


def cmd_overlay(args: argparse.Namespace, reporter: Reporter) -> int:
    """`flosub overlay SUBS`: the subtitles alone on a transparent video (for editors)."""
    from legendaria_engine import media

    subs = Path(args.file).expanduser()
    config = load_config()
    style = check_style(config, args.style)
    transcript, cues, _ = load_subtitles(subs)
    source = transcript.source if transcript else (cues.source if cues else "")
    info = {"width": None, "fps": None, "duration": 0.0}
    if source and Path(source).is_file() and not (args.size and args.fps and args.duration):
        info = media.probe(Path(source), config)
    size = args.size or ((info["width"], info["height"]) if info["width"] else (1920, 1080))
    fps = args.fps or info["fps"] or 25.0
    text, _ = ass_for(subs, config, style, size)
    duration = args.duration or info["duration"]
    if not duration:
        ends = [c.end for c in cues.cues] if cues else []
        if transcript:
            ends = [s.end for s in transcript.segments]
        duration = max(ends, default=0.0) + 0.5
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else subs.parent / f"{subs.name.removesuffix('.json').removesuffix('.cues')}.overlay.mov"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    media.overlay(config, text, size, fps, duration, output, reporter)
    reporter.emit("done", outputs=[str(output)], style=style, size=list(size), fps=fps)
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
    t.add_argument("--format", type=parse_formats, help="comma-separated: json,cues,srt,vtt,ass")
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
        help="glossary file or library name (repeatable); the active glossary and legendaria-glossary.txt next to the media are used too",
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
        "--llm",
        dest="llm",
        action="store_true",
        default=None,
        help="EXPERIMENTAL: also use the LLM reviewer",
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

    llm_parser = sub.add_parser(
        "llm", help="(experimental) check the LLM reviewer's server, list providers"
    )
    llm_parser.add_argument("action", choices=["check", "providers"])
    llm_parser.add_argument("--provider")
    llm_parser.add_argument("--model", dest="llm_model")
    llm_parser.add_argument("--base-url")
    llm_parser.set_defaults(func=cmd_llm)

    g = sub.add_parser("glossary", help="manage the glossary library and add terms")
    g.add_argument(
        "action",
        choices=["list", "new", "use", "import", "export", "delete", "show", "path", "add"],
    )
    g.add_argument("values", nargs="*", help="NAME, FILE or ENTRY depending on the action")
    g.add_argument("--name", help="import: name in the library; add: library glossary to add to")
    g.add_argument("--media", help="add/show: the project glossary next to this media file")
    g.add_argument("--file", help="add/show: a specific glossary file")
    g.add_argument("--to", help="export: destination file")
    g.add_argument("--activate", action="store_true", help="new: make it the active glossary")
    g.add_argument("--overwrite", action="store_true", help="import: replace an existing one")
    g.set_defaults(func=cmd_glossary)

    e = sub.add_parser("export", help="turn a transcript (or cues) JSON into cues/SRT/VTT/ASS")
    e.add_argument("file", help="transcript JSON, or a cues JSON (e.g. edited in Blender)")
    e.add_argument(
        "--format", type=parse_formats, default=["srt"], help="comma-separated: cues,srt,vtt,ass"
    )
    e.add_argument("--style", help="cue style: subtitles (default), captions, pop, or your own")
    e.add_argument("--output", help="output path without extension (default: next to the JSON)")
    e.add_argument("--size", type=parse_size, help="ass: canvas WIDTHxHEIGHT (default: video)")
    e.set_defaults(func=cmd_export)

    b = sub.add_parser("burn", help="burn the subtitles into a copy of the video (needs FFmpeg)")
    b.add_argument("file", help="the video")
    b.add_argument("--subs", help="transcript, cues or .ass (default: VIDEO.json next to it)")
    b.add_argument("--style", help="cue style and look (see `flosub config show`)")
    b.add_argument("--output", help="new video (default: VIDEO.subtitled.mp4)")
    b.set_defaults(func=cmd_burn)

    o = sub.add_parser(
        "overlay", help="render the subtitles alone on a transparent .mov (needs FFmpeg)"
    )
    o.add_argument("file", help="transcript, cues or .ass")
    o.add_argument("--style", help="cue style and look")
    o.add_argument("--size", type=parse_size, help="WIDTHxHEIGHT (default: the source video)")
    o.add_argument("--fps", type=float, help="frame rate (default: the source video, else 25)")
    o.add_argument("--duration", type=float, help="seconds (default: the source or last cue)")
    o.add_argument("--output", help="the .mov to write (default: NAME.overlay.mov)")
    o.set_defaults(func=cmd_overlay)

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
