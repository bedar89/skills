import json
import math
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def youtube_url(value):
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or parsed.username or parsed.password:
        raise ValueError("Use a public YouTube URL.")
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        video_id = parsed.path.strip("/")
    elif host in ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"):
        parts = parsed.path.strip("/").split("/")
        video_id = (parse_qs(parsed.query).get("v", [""])[0] if parsed.path == "/watch"
                    else parts[1] if len(parts) == 2 and parts[0] in ("shorts", "live") else "")
    else:
        raise ValueError("Use a public YouTube URL.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("The YouTube URL needs one valid video ID.")
    return f"https://www.youtube.com/watch?v={video_id}"


def seconds(value):
    fields = value.split(":")
    if not 1 <= len(fields) <= 3:
        raise ValueError("Use seconds, MM:SS or HH:MM:SS.")
    total = 0.0
    for field in fields:
        if not re.fullmatch(r"\d+(?:\.\d+)?", field):
            raise ValueError("Timestamps must be nonnegative numbers.")
        total = total * 60 + float(field)
    if not math.isfinite(total):
        raise ValueError("Timestamp must be finite.")
    return total


def clock(value):
    value = int(value)
    return f"{value // 3600:02}:{value // 60 % 60:02}:{value % 60:02}"


def workdir(parent):
    if parent:
        Path(parent).expanduser().mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="watch-youtube-", dir=Path(parent).expanduser() if parent else None)).resolve()


def save_report(directory, evidence, text):
    (directory / "evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = directory / "report.md"
    report.write_text(text, encoding="utf-8")
    print(f"Report: {report}")
    print(f"Evidence: {directory / 'evidence.json'}")
