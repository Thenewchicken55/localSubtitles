from pathlib import Path


def _format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def segments_to_srt(segments, max_line_width: int = 42) -> str:
    entries = []
    for i, segment in enumerate(segments, start=1):
        start = _format_timestamp(segment.start)
        end = _format_timestamp(segment.end)
        text = segment.text.strip()

        if max_line_width and len(text) > max_line_width:
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
            text = "\n".join(lines)

        entries.append(f"{i}\n{start} --> {end}\n{text}\n")

    return "\n".join(entries)


def write_srt(content: str, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.write_text(content, encoding="utf-8-sig")
    return output_path
