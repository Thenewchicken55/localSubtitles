# localSubtitles — Implementation Plan

## 1. Tech Stack Decision

### Chosen Stack

| Layer            | Choice                         | Why                                                                 |
|------------------|--------------------------------|----------------------------------------------------------------------|
| Language         | Python 3.10+                   | Best ML/Audio ecosystem, wide tooling, platform-agnostic             |
| STT Engine       | **faster-whisper**             | 4× faster than openai-whisper, 4× less memory, built-in Silero VAD  |
| Whisper Model    | `large-v3-turbo` (default)     | 809M params, 99 languages, ~6 GB VRAM, near-identical accuracy to large-v3 |
| Audio Extraction | `ffmpeg` (via subprocess)      | Industry standard, handles any container/codec, battle-tested       |
| VAD              | Silero VAD (built-in)          | Skips silence automatically, saves compute on long videos           |
| Compute Type     | `int8` (CPU) / `float16` (GPU) | INT8 for CPU (SIMD), FP16 for GPU (CUDA/MPS)                        |
| CLI              | `argparse`                     | Zero dependencies, stdlib, sufficient for our needs                 |
| Subtitle Format  | SRT                            | Universal — works in every video player/editor                      |
| Testing          | `pytest` + `pytest-mock`       | Lightweight, powerful, industry standard                            |
| Packaging        | `pip` + `requirements.txt`     | Simple, universal                                                   |

### Why NOT alternatives

| Alternative         | Rejected because                                                                 |
|---------------------|----------------------------------------------------------------------------------|
| openai-whisper      | 4× slower, 4× more memory, no built-in VAD, PyTorch overhead                    |
| whisper.cpp         | Great perf but C++ integration adds complexity; faster-whisper gives same speed via Python |
| WhisperX            | Overkill (diarization not needed), more complex setup, ~20% slower              |
| Canary Qwen 2.5B    | English-only; we need multilingual                                              |
| Parakeet TDT        | Streaming-focused; worse accuracy than Whisper on long-form audio               |
| Vosk                | Significantly less accurate than Whisper for general use                        |
| Cloud APIs (Rev, etc) | Violates "free" requirement, requires internet, privacy concerns               |

### Performance Estimates (1 hr audio, AMD RX 7700 XT)

| Model        | OpenAI Whisper | faster-whisper |
|--------------|----------------|----------------|
| tiny         | ~12 min        | ~1.5 min       |
| base         | ~20 min        | ~2.5 min       |
| small        | ~35 min        | ~5 min         |
| medium       | ~55 min        | ~9 min         |
| large-v3     | ~90 min        | ~18 min        |
| large-v3-turbo | ~60 min      | ~12 min        |

*Sources: faster-whisper benchmarks, WhisperX comparison, community testing. Times are approximate.*

---

## 2. Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Video File  │───▶│  Audio Extr. │───▶│ Transcription│───▶│  SRT Output  │
│  (.mp4,etc)  │    │  (ffmpeg)    │    │ (fst-whisper)│    │  (formatter) │
└─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                          │                   │
                      temp .wav          VAD + model
```

**Pipeline flow:**
1. Validate input file
2. Extract audio stream to temporary WAV (16kHz mono PCM)
3. Run faster-whisper with VAD, beam search, word timestamps
4. Convert segment/word data to SRT format
5. Write .srt alongside original video

### Key design decisions for reliability on long videos

- **Streaming extraction**: Extract audio as we go; no need to hold entire file in memory
- **VAD pre-processing**: Silero VAD removes silence before transcription, reducing compute by 30–50%
- **Chunked processing**: faster-whisper processes audio in chunks internally, avoiding OOM on long files
- **Progress reporting**: Show progress per-second-of-audio-processed
- **Crash recovery**: Interim results written periodically (future enhancement)
- **Validation step**: Verify output SRT is well-formed after generation

---

## 3. Project Structure

```
C:\Users\eliaa\Code\localSubtitles\
├── src/
│   └── localsub/
│       ├── __init__.py          # Version
│       ├── __main__.py          # `python -m localsub` entry
│       ├── cli.py               # Argument parsing, orchestration
│       ├── audio.py             # Audio extraction via ffmpeg
│       ├── transcribe.py        # faster-whisper wrapper
│       ├── subtitle.py          # SRT generation
│       └── utils.py             # Helpers (validation, temp files)
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures
│   ├── test_audio.py
│   ├── test_transcribe.py
│   ├── test_subtitle.py
│   └── test_utils.py
├── .gitignore
├── requirements.txt
├── README.md
└── PLAN.md
```

---

## 4. Implementation Steps

### Phase A — Foundation (Steps 1–3)
| Step | Task | Description |
|------|------|-------------|
| A1 | Project scaffolding | Create `.gitignore`, `requirements.txt`, package skeleton |
| A2 | `src/localsub/utils.py` | File validation, temp file management, SRT validation |
| A3 | `src/localsub/audio.py` | ffmpeg-based audio extraction to 16kHz mono WAV |

### Phase B — Core Engine (Steps 4–6)
| Step | Task | Description |
|------|------|-------------|
| B4 | `src/localsub/transcribe.py` | faster-whisper wrapper with VAD, model selection, progress |
| B5 | `src/localsub/subtitle.py` | Convert segments to SRT with proper formatting |
| B6 | `src/localsub/cli.py` | argparse CLI, orchestrate full pipeline |

### Phase C — Entry Points & Packaging (Steps 7–8)
| Step | Task | Description |
|------|------|-------------|
| C7 | `src/localsub/__main__.py` | `python -m localsub` support |
| C8 | Testing | pytest tests for every module |

### Phase D — Quality & Docs (Steps 9–11)
| Step | Task | Description |
|------|------|-------------|
| D9 | Edge-case hardening | Unicode, special chars, very long lines, missing ffmpeg |
| D10 | `README.md` | Full usage docs, examples, troubleshooting |
| D11 | Git + GitHub | Init repo, commit history, push to GitHub |

---

## 5. Commit Strategy

| Commit # | Scope | Files |
|----------|-------|-------|
| 1 | Initial scaffold | `.gitignore`, `requirements.txt`, `src/localsub/__init__.py`, `src/localsub/__main__.py` |
| 2 | Utils + Audio | `utils.py`, `audio.py` + their tests |
| 3 | Transcription | `transcribe.py` + tests |
| 4 | Subtitle + CLI | `subtitle.py`, `cli.py` + tests |
| 5 | Package setup | `setup.py` or `pyproject.toml` (tbd) |
| 6 | README + docs | `README.md`, final polish |
| 7 | GitHub remote | `gh repo create`, push all |

---

## 6. Testing Strategy

| Module | What to test | How |
|--------|-------------|-----|
| `audio.py` | ffmpeg detection, extraction success, invalid input | Mock subprocess, test with small WAV fixture |
| `transcribe.py` | Model loading, transcription call, VAD toggle | Mock faster-whisper, verify params passed correctly |
| `subtitle.py` | Segment→SRT conversion, edge cases (unicode, empty) | Pure function tests, golden file comparison |
| `utils.py` | File validation, temp dir creation, extension parsing | Pure function tests |
| `cli.py` | Arg parsing, pipeline integration | Use CliRunner (or manual arg test) |

---

## 7. Future Enhancements (post-MVP)

- [ ] **Batch mode**: Process multiple videos in one command
- [ ] **Crash recovery**: Save interim results, resume on interrupt
- [ ] **VTT support**: Additional subtitle format
- [ ] **Translation**: Translate subtitles to another language
- [ ] **Word-level timestamps**: More precise subtitle sync
- [ ] **Burn-in**: Optional hardcode subtitles into video via ffmpeg
- [ ] **Diarization**: Label speakers (requires WhisperX)
- [ ] **GUI**: Simple web UI or Tkinter frontend
