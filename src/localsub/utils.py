import os
import re
import tempfile
from pathlib import Path

VALID_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
VALID_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"}
VALID_MEDIA_EXTENSIONS = VALID_VIDEO_EXTENSIONS | VALID_AUDIO_EXTENSIONS


def is_supported_media(file_path: str | Path) -> bool:
    ext = Path(file_path).suffix.lower()
    return ext in VALID_MEDIA_EXTENSIONS


def get_output_srt_path(input_path: str | Path) -> Path:
    return Path(input_path).with_suffix(".srt")


def create_temp_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="localsub_"))


def validate_input_file(file_path: str | Path) -> Path:
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    if not p.is_file():
        raise ValueError(f"Path is not a file: {p}")
    if not is_supported_media(p):
        raise ValueError(
            f"Unsupported file format: {p.suffix}. "
            f"Supported: {', '.join(sorted(VALID_MEDIA_EXTENSIONS))}"
        )
    return p


SRT_TIMECODE_RE = re.compile(
    r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$"
)


def validate_srt(content: str) -> bool:
    lines = [l.strip() for l in content.strip().splitlines() if l.strip()]
    if not lines:
        return False
    i = 0
    while i < len(lines):
        if not lines[i].isdigit():
            return False
        i += 1
        if i >= len(lines) or not SRT_TIMECODE_RE.match(lines[i]):
            return False
        i += 1
        while i < len(lines) and lines[i].isdigit():
            return False
        while i < len(lines) and not lines[i].isdigit() and not SRT_TIMECODE_RE.match(lines[i]):
            i += 1
    return True
