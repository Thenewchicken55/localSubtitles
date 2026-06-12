from pathlib import Path
from localsub.subtitle import (
    _format_timestamp,
    _format_vtt_timestamp,
    segments_to_srt,
    segments_to_vtt,
    write_subtitles,
)


class TestFormatTimestamp:
    def test_zero(self):
        assert _format_timestamp(0) == "00:00:00,000"

    def test_basic_seconds(self):
        assert _format_timestamp(1.5) == "00:00:01,500"

    def test_minutes(self):
        assert _format_timestamp(65.0) == "00:01:05,000"

    def test_hours(self):
        assert _format_timestamp(3661.789) == "01:01:01,789"

    def test_rounding(self):
        assert _format_timestamp(1.9999) in ("00:00:02,000", "00:00:01,999")


class TestFormatVttTimestamp:
    def test_zero(self):
        assert _format_vtt_timestamp(0) == "00:00:00.000"

    def test_basic_seconds(self):
        assert _format_vtt_timestamp(1.5) == "00:00:01.500"


class TestSegmentsToSrt:
    def test_single_segment(self, sample_segments):
        result = segments_to_srt(sample_segments[:1])
        assert "1" in result
        assert "00:00:00,000 --> 00:00:02,500" in result
        assert "Hello world." in result

    def test_multiple_segments(self, sample_segments):
        result = segments_to_srt(sample_segments)
        assert result.count("-->") == 3
        assert "1\n" in result
        assert "2\n" in result
        assert "3\n" in result

    def test_line_wrapping(self, sample_segments):
        result = segments_to_srt(sample_segments, max_line_width=20)
        lines = result.splitlines()
        content_lines = [l for l in lines if l and not l[0].isdigit() and "-->" not in l]
        for line in content_lines:
            assert len(line) <= 20

    def test_empty_segments(self):
        result = segments_to_srt([])
        assert result == ""

    def test_unicode(self, sample_segments):
        sample_segments[0].text = "Cómo estás? 你好吗？"
        result = segments_to_srt(sample_segments[:1])
        assert "Cómo estás? 你好吗？" in result

    def test_word_refined_boundary(self):
        class FakeWord:
            def __init__(self, start, end, word):
                self.start = start
                self.end = end
                self.word = word

        class FakeSegment:
            def __init__(self):
                self.start = 0.0
                self.end = 10.0
                self.text = "Refined"
                self.words = [
                    FakeWord(0.5, 1.0, "Refined"),
                ]

        result = segments_to_srt([FakeSegment()])
        assert "00:00:00,500 --> 00:00:01,000" in result


class TestSegmentsToVtt:
    def test_basic(self, sample_segments):
        result = segments_to_vtt(sample_segments)
        assert result.startswith("WEBVTT")
        assert "00:00:00.000 --> 00:00:02.500" in result
        assert "Hello world." in result

    def test_empty(self):
        assert segments_to_vtt([]) == "WEBVTT\n"


class TestWriteSubtitles:
    def test_writes_utf8_bom(self, tmp_path):
        output = tmp_path / "out.srt"
        result = write_subtitles("1\n00:00:01,000 --> 00:00:02,000\nTest\n", output)
        assert result == output
        assert output.exists()
        content = output.read_bytes()
        assert content.startswith(b"\xef\xbb\xbf")

    def test_returns_path(self, tmp_path):
        output = tmp_path / "out.srt"
        result = write_subtitles("content", output)
        assert result == output
