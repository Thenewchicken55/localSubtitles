# localSubtitles

> Generate subtitles from videos entirely on your machine. Free, private, works on long videos.

[![asciicast](https://img.shields.io/badge/asciicast-demo-green.svg)](https://asciinema.org/a/REPLACE_ME)

`localsub` transcribes video/audio files into SRT/VTT subtitles using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — a 4x faster, 4x more memory-efficient reimplementation of OpenAI's Whisper. Everything runs locally; no data ever leaves your computer.

## Quick Start

```bash
pip install -r requirements.txt
pip install -e .
localsub video.mp4
```

This outputs `video.srt` next to your video.

## Requirements

- **Python 3.10+**
- **ffmpeg** — [Install guide](https://ffmpeg.org/download.html) (must be on your PATH)
- ~6 GB RAM for default model (`large-v3-turbo`). Smaller models use less.

## Usage

```bash
localsub <input_file...> [options]
```

### Options

| Argument | Default | Description |
|----------|---------|-------------|
| `input` | — | Path(s) to video/audio files (batch supported) |
| `-o, --output` | `input.srt` | Output path (single input only) |
| `--model` | `large-v3-turbo` | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo` |
| `--device` | `auto` | Device: `auto`, `cpu`, `cuda` |
| `--compute-type` | `default` | `int8` (CPU), `float16` (GPU), `float32` |
| `--language` | auto-detect | Language code (e.g. `en`, `fr`, `es`) |
| `--no-vad` | off | Disable silence-skipping (VAD) |
| `--beam-size` | `5` | Beam search width (higher = slower but more accurate) |
| `--format` | `srt` | Output format: `srt`, `vtt`, or `both` |
| `--force` | off | Re-transcribe ignoring cached results |
| `--version` | — | Show version |

### Examples

```bash
# Basic usage
localsub my_video.mp4

# VTT format
localsub talk.mp4 --format vtt

# Both SRT and VTT
localsub video.mp4 --format both

# Specify output path
localsub talk.mp4 -o subtitles.srt

# Smaller model for faster processing on modest hardware
localsub lecture.mp4 --model base --compute-type int8

# Force CPU with int8 quantization
localsub video.mkv --device cpu --compute-type int8

# French video
localsub video.mp4 --language fr

# Disable VAD (if speech is being incorrectly filtered)
localsub video.mp4 --no-vad

# Batch process multiple videos
localsub ep1.mp4 ep2.mp4 ep3.mp4

# Re-transcribe (ignore cache)
localsub video.mp4 --force
```

### Supported Input Formats

**Video:** MP4, MKV, AVI, MOV, WMV, FLV, WebM, M4V  
**Audio:** MP3, WAV, FLAC, AAC, OGG, M4A, WMA

## How It Works

```
Video file ──▶ ffmpeg extracts audio ──▶ faster-whisper transcribes ──▶ SRT/VTT file
```

1. **ffmpeg** extracts the audio stream to 16 kHz mono WAV
2. **faster-whisper** transcribes with word-level timestamps and Silero VAD (skips silence automatically)
3. Subtitles are formatted with word-accurate boundaries and written to disk

For long videos:
- **VAD** removes non-speech segments before transcription, saving 30–50% compute time
- **Progress bar** shows real-time transcription progress
- **Cache** saves results to `~/.cache/localsub/` so re-running the same file is instant
- **Audio validation** detects files with no audio stream before starting

## Model Sizes

| Model | Parameters | RAM/VRAM | Speed | Quality |
|-------|-----------|----------|-------|---------|
| `tiny` | 39M | ~1 GB | Very fast | Lower |
| `base` | 74M | ~1 GB | Fast | Fair |
| `small` | 244M | ~2 GB | Moderate | Good |
| `medium` | 769M | ~5 GB | Slow | Very good |
| `large-v3` | 1.55B | ~10 GB | Slowest | Best |
| `large-v3-turbo` | 809M | ~6 GB | Fast | Near best |

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest

# Run tests with coverage
pytest --cov=localsub

# Lint
ruff check src/

# Setup pre-commit hooks
pre-commit install
```

## Why faster-whisper?

| | OpenAI Whisper | faster-whisper |
|---|---|---|
| Speed | Baseline | **4x faster** |
| Memory | High (PyTorch) | **4x less** (CTranslate2) |
| VAD | None | **Built-in** (Silero) |
| Long audio | Prone to OOM | **Chunked, efficient** |
| Word timestamps | Basic | **Per-word with start/end** |
| License | MIT | MIT |

Benchmarks against openai-whisper on 1 hour audio (from community testing):
- **tiny**: ~1.5 min vs ~12 min
- **small**: ~5 min vs ~35 min
- **large-v3**: ~18 min vs ~90 min

## License

MIT
