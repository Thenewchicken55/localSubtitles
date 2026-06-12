import pytest
from pathlib import Path
from localsub.utils import (
    is_supported_media,
    get_output_srt_path,
    validate_input_file,
    validate_srt,
    VALID_MEDIA_EXTENSIONS,
)


class TestIsSupportedMedia:
    def test_video_extensions(self):
        for ext in [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"]:
            assert is_supported_media(f"file{ext}")

    def test_audio_extensions(self):
        for ext in [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"]:
            assert is_supported_media(f"file{ext}")

    def test_unsupported_extension(self):
        assert not is_supported_media("file.txt")
        assert not is_supported_media("file.pdf")
        assert not is_supported_media("file")

    def test_case_insensitive(self):
        assert is_supported_media("file.MP4")
        assert is_supported_media("file.WAV")


class TestGetOutputSrtPath:
    def test_replaces_extension(self):
        assert get_output_srt_path("video.mp4") == Path("video.srt")

    def test_preserves_full_path(self):
        result = get_output_srt_path("/home/user/video.mkv")
        assert result == Path("/home/user/video.srt")

    def test_handles_multiple_dots(self):
        assert get_output_srt_path("my.video.file.mp4") == Path("my.video.file.srt")


class TestValidateInputFile:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_input_file("/nonexistent/file.mp4")

    def test_unsupported_format(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("content")
        with pytest.raises(ValueError, match="Unsupported file format"):
            validate_input_file(p)

    def test_valid_file(self, sample_video_path):
        result = validate_input_file(sample_video_path)
        assert result == sample_video_path


class TestValidateSrt:
    def test_empty_content(self):
        assert not validate_srt("")
        assert not validate_srt("   ")

    def test_valid_srt_single_entry(self):
        srt = "1\n00:00:01,000 --> 00:00:04,000\nHello world\n"
        assert validate_srt(srt)

    def test_valid_srt_multi_entry(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:04,000\nHello world\n\n"
            "2\n00:00:05,000 --> 00:00:10,000\nSecond line\n"
        )
        assert validate_srt(srt)

    def test_valid_srt_multiline_text(self):
        srt = (
            "1\n00:00:01,000 --> 00:00:05,000\n"
            "Line one\nLine two\nLine three\n\n"
            "2\n00:00:06,000 --> 00:00:10,000\nLast line\n"
        )
        assert validate_srt(srt)

    def test_invalid_srt_no_number(self):
        srt = "00:00:01,000 --> 00:00:04,000\nHello\n"
        assert not validate_srt(srt)

    def test_invalid_srt_bad_timecode(self):
        srt = "1\n00:00:01,000 -> 00:00:04,000\nHello\n"
        assert not validate_srt(srt)

    def test_valid_srt_with_unicode(self):
        srt = "1\n00:00:01,000 --> 00:00:04,000\nBonjour le monde\n"
        assert validate_srt(srt)
