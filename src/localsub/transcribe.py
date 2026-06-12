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
    word_timestamps: bool = True,
    progress_callback=None,
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
        word_timestamps=word_timestamps,
    )

    detected_language = info.language
    duration = info.duration

    collected = []
    for segment in segments:
        collected.append(segment)
        if progress_callback:
            progress_callback(segment.end / duration if duration > 0 else 0)

    return collected, detected_language, duration
