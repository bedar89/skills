#!/usr/bin/env python3
"""Collect a YouTube transcript and bounded stills without cloud inference."""
import argparse
import html
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from common import clock, save_report, seconds, workdir, youtube_url


def run(command, timeout=300):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise ValueError(f"Required executable missing: {command[0]}") from None
    except subprocess.TimeoutExpired:
        raise ValueError(f"{command[0]} timed out; no automatic retry.") from None
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        detail = lines[-1] if lines else "No diagnostic received."
        detail = re.sub(r"https?://\S+", "[URL omitted]", detail)
        detail = re.sub(r"(?i)(bearer\s+|(?:token|password|api[_-]?key)\s*[=:]\s*)\S+", r"\1[redacted]", detail)
        status = re.search(r"\bHTTP(?: Error)?\s+(\d{3})\b", result.stderr, re.I)
        code = f"HTTP {status[1]}" if status else f"exit {result.returncode}"
        raise ValueError(f"{command[0]} failed ({code}): {detail[:300]}. No automatic retry.")
    return result.stdout


def caption_track(info):
    manual = {k: v for k, v in (info.get("subtitles") or {}).items() if v and k != "live_chat"}
    auto = {k: v for k, v in (info.get("automatic_captions") or {}).items() if v}
    originals = [k for k in auto if k.endswith("-orig")]
    language = originals[0][:-5] if len(originals) == 1 else info.get("language")
    for kind, tracks in (("manual", manual), ("automatic", auto)):
        matches = [k for k in tracks if language and k.removesuffix("-orig").split("-")[0] == language.split("-")[0]]
        if matches:
            chosen = min(matches, key=lambda k: (kind == "automatic" and k != f"{language}-orig", k != language, k))
            return kind, chosen, True
    for kind, tracks in (("manual", manual), ("automatic", auto)):
        if tracks:
            return kind, min(tracks, key=lambda k: (not k.startswith("en"), k)), False
    return None


def compact_transcript(vtt, *, rolling=False):
    output, previous, previous_end = [], [], 0
    for block in re.split(r"\r?\n\r?\n", vtt):
        lines = block.splitlines()
        for index, line in enumerate(lines):
            match = re.match(r"\s*((?:\d{2}:)?\d{2}:\d{2}\.\d{3})\s+-->\s+((?:\d{2}:)?\d{2}:\d{2}\.\d{3})", line)
            if not match:
                continue
            text = html.unescape(re.sub(r"<[^>]*>", "", " ".join(lines[index + 1:]))).strip()
            words = text.split()
            overlap = 0
            if rolling and seconds(match[1]) <= previous_end + 0.1:
                for size in range(1, min(len(previous), len(words)) + 1):
                    if previous[-size:] == words[:size]:
                        overlap = size
            fresh = words[overlap:]
            if fresh:
                output.append(f"[{match[1]}] {' '.join(fresh)}")
            previous, previous_end = words, seconds(match[2])
            break
    return "\n".join(output) + ("\n" if output else "")


def collect(args):
    source = args.source
    is_url = source.startswith(("http:", "https:"))
    if is_url:
        source = youtube_url(source)
    else:
        source = str(Path(source).expanduser().resolve(strict=True))
    cues = [seconds(t.strip()) for t in args.timestamps.split(",")] if args.timestamps else None
    if cues and len(cues) > args.max_frames:
        raise ValueError("Requested timestamps exceed --max-frames; split the request.")
    directory = workdir(args.out_dir)
    evidence = {"route": "local", "source": source, "frames": [], "caption": None, "errors": []}
    media = None
    if is_url:
        yt = ["yt-dlp", "--ignore-config", "--no-playlist", "--retries", "0", "--fragment-retries", "0", "--socket-timeout", "20"]
        runtime = next((name for name in ("deno", "node", "bun") if shutil.which(name)), None)
        if runtime:
            yt += ["--js-runtimes", runtime]
        try:
            info = json.loads(run(yt + ["--skip-download", "--dump-single-json", source]))
            evidence["metadata"] = {k: info.get(k) for k in ("title", "channel", "upload_date", "duration", "description")}
            track = caption_track(info)
            if track and not args.skip_captions:
                kind, language, original = track
                try:
                    run(yt + ["--skip-download", "--no-write-subs", "--no-write-auto-subs",
                              "--write-subs" if kind == "manual" else "--write-auto-subs",
                              "--sub-langs", language, "--sub-format", "vtt", "-o", str(directory / "captions.%(ext)s"), source])
                    files = sorted(directory.glob("captions*.vtt"))
                    if files and files[0].stat().st_size:
                        transcript = compact_transcript(files[0].read_text(encoding="utf-8"), rolling=kind == "automatic")
                        if not transcript:
                            raise ValueError("Caption track contains no usable VTT cues.")
                        transcript_path = directory / "transcript.txt"
                        transcript_path.write_text(transcript, encoding="utf-8")
                        evidence["caption"] = {"path": str(files[0]), "kind": kind, "language": language,
                                               "original_language_verified": original,
                                               "transcript": str(transcript_path)}
                except ValueError as exc:
                    evidence["errors"].append(f"Captions: {exc}")
        except (ValueError, KeyError) as exc:
            evidence["errors"].append(f"Metadata: {exc}")
        if not args.transcript_only:
            try:
                media_path = run(yt + ["--no-progress", "--no-write-subs", "--no-write-auto-subs",
                                      "-f", "bestvideo[height<=1080]/best[height<=1080]",
                                      "-o", str(directory / "video.%(ext)s"), "--print", "after_move:filepath", source],
                                     timeout=args.download_timeout).strip().splitlines()
                media = Path(media_path[-1]) if media_path else None
                if not media or not media.is_file():
                    raise ValueError("yt-dlp did not return a downloaded video.")
            except ValueError as exc:
                evidence["errors"].append(f"Video: {exc}")
    elif not args.transcript_only:
        media = Path(source)
    if media:
        evidence["media"] = str(media)
        try:
            probe = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(media)]))
            duration = float(probe["format"]["duration"])
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("Media duration must be positive and finite.")
            evidence["duration"] = duration
            last = max(0, duration - min(0.25, duration / 2))
            points = cues if cues is not None else [i * last / max(1, args.max_frames - 1) for i in range(args.max_frames)]
            if any(t >= duration for t in points):
                raise ValueError("A requested timestamp is beyond the video duration.")
            for index, timestamp in enumerate(points):
                path = directory / f"frame-{index:03}.jpg"
                run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(timestamp), "-i", str(media),
                     "-frames:v", "1", "-vf", f"scale={args.width}:-2", "-q:v", "3", str(path)])
                if not path.is_file() or not path.stat().st_size:
                    raise ValueError(f"No frame decoded at {clock(timestamp)}.")
                evidence["frames"].append({"requested_seconds": timestamp, "path": str(path)})
        except (ValueError, KeyError) as exc:
            evidence["errors"].append(f"Frames: {exc}")
    if not evidence["caption"]:
        evidence["errors"].append("Captions skipped in this run; use earlier transcript if available." if args.skip_captions
                                  else "No transcript available; speech was not transcribed.")
    if not args.transcript_only and not evidence["frames"]:
        evidence["errors"].append("No visual evidence available.")
    useful = bool(evidence["caption"] or evidence["frames"])
    evidence["status"] = "unavailable" if not useful else "partial" if evidence["errors"] else "complete"
    report = ["# Local video evidence", f"Source: {source}", f"Media: {evidence.get('media', 'unavailable')}",
              f"Status: {evidence['status']}", "", "## Metadata",
              "```json", json.dumps(evidence.get("metadata", {}), ensure_ascii=False, indent=2), "```", "", "## Transcript",
              "```json", json.dumps(evidence["caption"], ensure_ascii=False), "```", "", "## Sampled frames",
              "Stills are samples, not continuous viewing; timestamps are requested source times."]
    report += [f"- {clock(f['requested_seconds'])}: `{f['path']}`" for f in evidence["frames"]]
    report += ["", "## Missing evidence and errors"] + [f"- {error}" for error in evidence["errors"]]
    save_report(directory, evidence, "\n".join(report) + "\n")
    return 1 if not useful else 2 if evidence["errors"] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="YouTube URL or a local video to reuse")
    parser.add_argument("--timestamps", help="Comma-separated source timestamps; replaces interval sampling")
    parser.add_argument("--max-frames", type=int, default=24)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--transcript-only", action="store_true")
    parser.add_argument("--skip-captions", action="store_true", help="Do not request captions again after a rate limit or existing transcript")
    parser.add_argument("--download-timeout", type=int, default=3600, help="Whole-video download timeout in seconds")
    parser.add_argument("--out-dir", help="Parent for a new temporary run directory")
    args = parser.parse_args()
    if not 1 <= args.max_frames <= 100 or not 320 <= args.width <= 1920:
        parser.error("Use 1..100 frames and a width of 320..1920 pixels.")
    if args.download_timeout <= 0:
        parser.error("--download-timeout must be positive.")
    if args.transcript_only and args.timestamps:
        parser.error("--transcript-only cannot provide timestamp frames.")
    if args.transcript_only and args.skip_captions:
        parser.error("--transcript-only and --skip-captions collect no content evidence together.")
    try:
        return collect(args)
    except (ValueError, OSError) as exc:
        print(f"Local evidence unavailable: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
