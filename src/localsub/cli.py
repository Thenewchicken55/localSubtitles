import argparse
import sys
from pathlib import Path

from localsub import __version__
from localsub.audio import check_ffmpeg, extract_audio
from localsub.subtitle import segments_to_srt, write_srt
from localsub.transcribe import transcribe
from localsub.utils import (
    create_temp_dir,
    get_output_srt_path,
    validate_input_file,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="localsub",
        description="Generate subtitles from video/audio files using local AI.",
    )
    parser.add_argument(
        "input",
        help="Path to a video or audio file",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output .srt path (default: same as input with .srt extension)",
    )
    parser.add_argument(
        "--model",
        default="large-v3-turbo",
        help="Whisper model size: tiny, base, small, medium, large-v3, large-v3-turbo (default: large-v3-turbo)",
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
        "--version",
        action="version",
        version=f"localsub {__version__}",
    )
    return parser


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

    try:
        input_path = validate_input_file(args.input)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    output_path: Path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_output_srt_path(input_path)

    print(f"Input:  {input_path}")
    print(f"Model:  {args.model}")
    print(f"Device: {args.device}")

    temp_dir = create_temp_dir()
    temp_wav = temp_dir / "audio.wav"

    try:
        print("Extracting audio...", end=" ", flush=True)
        extract_audio(input_path, temp_wav)
        print("done.")

        print("Transcribing...", end=" ", flush=True)
        segments, detected_lang = transcribe(
            audio_path=temp_wav,
            model_name=args.model,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
            vad_filter=not args.no_vad,
            beam_size=args.beam_size,
            verbose=True,
        )
        print(f"done (detected: {detected_lang}).")

        srt_content = segments_to_srt(segments)
        write_srt(srt_content, output_path)
        print(f"Subtitles written to: {output_path}")
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1
    finally:
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    return 0
