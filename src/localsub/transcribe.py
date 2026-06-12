from pathlib import Path
from faster_whisper import WhisperModel


def transcribe(
    audio_path: str | Path,
    model_name: str = "large-v3-turbo",
    device: str = "auto",
    compute_type: str = "default",
    language: str | None = None,
    vad_filter: bool = True,
    beam_size: int = 5,
    verbose: bool = False,
):
    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
    )

    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=vad_filter,
        beam_size=beam_size,
    )

    detected_language = info.language
    if verbose:
        duration = info.duration
        print(f"Detected language: {detected_language} ({info.language_probability*100:.1f}%)")
        print(f"Audio duration: {duration:.1f}s")

    return segments, detected_language
