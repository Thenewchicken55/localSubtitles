import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from tqdm import tqdm

from localsub import __version__
from localsub.audio import check_ffmpeg, extract_audio, has_audio_stream
from localsub.subtitle import segments_to_srt, segments_to_vtt, write_subtitles
from localsub.transcribe import transcribe
from localsub.utils import (
    create_temp_dir,
    get_output_srt_path,
    get_output_vtt_path,
    validate_input_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="localsub",
        description="Generate subtitles from video/audio files using local AI.",
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Path(s) to video or audio files",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output subtitle path (only with single input)",
    )
    parser.add_argument(
        "--model",
        default="large-v3-turbo",
        help="Whisper model: tiny, base, small, medium, large-v3, large-v3-turbo (default: large-v3-turbo)",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Device: auto, cpu, cuda (default: auto)",
    )
    parser.add_argument(
        "--compute-type",
        default="default",
        help="Compute type: default, int8, float16, float32 (default: default)",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Language code (auto-detect by default, e.g. en, fr, es)",
    )
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable voice activity detection",
    )
    parser.add_argument(
        "--beam-size",
        type=int,
        default=5,
        help="Beam size for decoding (default: 5)",
    )
    parser.add_argument(
        "--format",
        choices=["srt", "vtt", "both"],
        default="srt",
        help="Subtitle format(s) to generate (default: srt)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-transcribe even if cached results exist",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"localsub {__version__}",
    )
    return parser


def get_cache_dir() -> Path:
    cache = Path.home() / ".cache" / "localsub"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def cache_key(input_path: Path, model: str, language: str | None, vad: bool, beam: int) -> str:
    import hashlib
    raw = f"{input_path.resolve()}:{input_path.stat().st_size}:{input_path.stat().st_mtime}:{model}:{language}:{vad}:{beam}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_cache(cache_dir: Path, key: str) -> list | None:
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def save_cache(cache_dir: Path, key: str, segments_data: list) -> None:
    cache_file = cache_dir / f"{key}.json"
    try:
        cache_file.write_text(
            json.dumps(segments_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def segment_to_dict(segment) -> dict:
    words = []
    if hasattr(segment, "words") and segment.words:
        words = [{"start": w.start, "end": w.end, "word": w.word} for w in segment.words]
    return {
        "start": segment.start,
        "end": segment.end,
        "text": segment.text,
        "words": words,
    }


def dict_to_segment(d: dict):
    return type("Segment", (), {
        "start": d["start"],
        "end": d["end"],
        "text": d["text"],
        "words": [type("Word", (), {"start": w["start"], "end": w["end"], "word": w["word"]})() for w in d.get("words", [])],
    })


def process_file(
    input_path: Path,
    args: argparse.Namespace,
) -> int:
    print(f"\n{'='*60}")
    print(f"Processing: {input_path.name}")
    print(f"{'='*60}")

    output_srt: Path | None = None
    output_vtt: Path | None = None

    if args.output:
        if len(args.inputs) > 1:
            print("Error: --output cannot be used with multiple inputs.", file=sys.stderr)
            return 1
        out = Path(args.output)
        if args.format in ("srt", "both"):
            output_srt = out.with_suffix(".srt") if out.suffix != ".srt" else out
        if args.format in ("vtt", "both"):
            output_vtt = out.with_suffix(".vtt") if out.suffix != ".vtt" else out
    else:
        if args.format in ("srt", "both"):
            output_srt = get_output_srt_path(input_path)
        if args.format in ("vtt", "both"):
            output_vtt = get_output_vtt_path(input_path)

    print(f"Model:  {args.model}")
    print(f"Device: {args.device}")

    is_video = input_path.suffix.lower() in {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"
    }

    if is_video and not has_audio_stream(input_path):
        print(f"Error: No audio stream found in: {input_path}", file=sys.stderr)
        return 1

    cache_dir = get_cache_dir()
    key = cache_key(
        input_path, args.model, args.language, not args.no_vad, args.beam_size
    )

    cached = None if args.force else load_cache(cache_dir, key)
    if cached is not None:
        print("Using cached transcription.")
        segments = [dict_to_segment(s) for s in cached]
    else:
        temp_dir = create_temp_dir()
        temp_wav = temp_dir / "audio.wav"

        try:
            start_t = time.time()
            print("Extracting audio...", flush=True)
            extract_audio(input_path, temp_wav)
            print(f"Audio extracted ({temp_wav.stat().st_size / 1024:.0f} KB).")

            with tqdm(total=100, desc="Transcribing", unit="%", leave=True) as pbar:
                def on_progress(pct: float):
                    pbar.n = int(pct * 100)
                    pbar.refresh()

                segments_raw, detected_lang, duration = transcribe(
                    audio_path=temp_wav,
                    model_name=args.model,
                    device=args.device,
                    compute_type=args.compute_type,
                    language=args.language,
                    vad_filter=not args.no_vad,
                    beam_size=args.beam_size,
                    word_timestamps=True,
                    progress_callback=on_progress,
                )
                pbar.n = 100
                pbar.refresh()

            elapsed = time.time() - start_t
            print(f"Transcribed in {elapsed:.0f}s ({duration / elapsed:.1f}x realtime).")
            print(f"Detected language: {detected_lang}")

            segments = segments_raw
            save_cache(cache_dir, key, [segment_to_dict(s) for s in segments])

        except KeyboardInterrupt:
            print("\nInterrupted.", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"\nError during transcription: {e}", file=sys.stderr)
            return 1
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    try:
        if output_srt:
            srt_content = segments_to_srt(segments)
            write_subtitles(srt_content, output_srt)
            print(f"SRT: {output_srt}")

        if output_vtt:
            vtt_content = segments_to_vtt(segments)
            write_subtitles(vtt_content, output_vtt)
            print(f"VTT: {output_vtt}")
    except Exception as e:
        print(f"Error writing subtitles: {e}", file=sys.stderr)
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    ffmpeg_info = check_ffmpeg()
    if ffmpeg_info is None:
        print(
            "Error: ffmpeg not found. Install ffmpeg and ensure it is on your PATH.",
            file=sys.stderr,
        )
        return 1

    if args.output and len(args.inputs) > 1:
        print("Error: --output cannot be used with multiple input files.", file=sys.stderr)
        return 1

    exit_code = 0
    for input_arg in args.inputs:
        try:
            input_path = validate_input_file(input_arg)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            exit_code = 1
            continue

        code = process_file(input_path, args)
        if code != 0:
            exit_code = code

    return exit_code
