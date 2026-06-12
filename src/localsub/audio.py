import json
import subprocess
from pathlib import Path


def check_ffmpeg() -> str | None:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.splitlines()[0]
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def check_ffprobe() -> bool:
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def has_audio_stream(input_path: str | Path) -> bool:
    input_path = Path(input_path)
    if not check_ffprobe():
        return True

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-select_streams", "a",
        str(input_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return True
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        return len(streams) > 0
    except (json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired):
        return True


def extract_audio(
    input_path: str | Path,
    output_path: str | Path,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not has_audio_stream(input_path):
        raise RuntimeError(f"No audio stream found in: {input_path}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", str(channels),
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=86400)
    except FileNotFoundError:
        raise RuntimeError("ffmpeg not found. Install ffmpeg and ensure it is on your PATH.")

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit code {result.returncode}):\n{result.stderr}"
        )

    if not output_path.exists():
        raise RuntimeError(f"ffmpeg completed but output file not found: {output_path}")

    return output_path
