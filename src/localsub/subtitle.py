from pathlib import Path


def _format_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_vtt_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def _refine_boundaries(segment) -> tuple[float, float]:
    if hasattr(segment, "words") and segment.words:
        word_list = list(segment.words)
        start = word_list[0].start
        end = word_list[-1].end
        return start, end
    return segment.start, segment.end


def _wrap_text(text: str, max_line_width: int = 42) -> str:
    if not max_line_width or len(text) <= max_line_width:
        return text
    words = text.split()
    lines = []
    current_line = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > max_line_width and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_len = len(word)
        else:
            current_line.append(word)
            current_len += len(word) + 1
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)


def segments_to_srt(segments, max_line_width: int = 42) -> str:
    entries = []
    for i, segment in enumerate(segments, start=1):
        start, end = _refine_boundaries(segment)
        text = _wrap_text(segment.text.strip(), max_line_width)
        entries.append(f"{i}\n{_format_timestamp(start)} --> {_format_timestamp(end)}\n{text}\n")
    return "\n".join(entries)


def segments_to_vtt(segments, max_line_width: int = 42) -> str:
    lines = ["WEBVTT", ""]
    for segment in segments:
        start, end = _refine_boundaries(segment)
        text = _wrap_text(segment.text.strip(), max_line_width)
        lines.append(f"{_format_vtt_timestamp(start)} --> {_format_vtt_timestamp(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def write_subtitles(content: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.write_text(content, encoding="utf-8-sig")
    return output_path
