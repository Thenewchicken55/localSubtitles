import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from localsub.cli import build_parser, main


@pytest.fixture
def parser():
    return build_parser()


class TestBuildParser:
    def test_accepts_one_input(self, parser):
        args = parser.parse_args(["video.mp4"])
        assert args.inputs == ["video.mp4"]
        assert args.model == "large-v3-turbo"

    def test_accepts_multiple_inputs(self, parser):
        args = parser.parse_args(["v1.mp4", "v2.mp4", "v3.mp4"])
        assert args.inputs == ["v1.mp4", "v2.mp4", "v3.mp4"]

    def test_output_option(self, parser):
        args = parser.parse_args(["video.mp4", "-o", "subs.srt"])
        assert args.output == "subs.srt"

    def test_model_option(self, parser):
        args = parser.parse_args(["video.mp4", "--model", "base"])
        assert args.model == "base"

    def test_device_option(self, parser):
        args = parser.parse_args(["video.mp4", "--device", "cpu"])
        assert args.device == "cpu"

    def test_compute_type(self, parser):
        args = parser.parse_args(["video.mp4", "--compute-type", "int8"])
        assert args.compute_type == "int8"

    def test_language_option(self, parser):
        args = parser.parse_args(["video.mp4", "--language", "fr"])
        assert args.language == "fr"

    def test_no_vad_flag(self, parser):
        args = parser.parse_args(["video.mp4", "--no-vad"])
        assert args.no_vad is True

    def test_vad_enabled_by_default(self, parser):
        args = parser.parse_args(["video.mp4"])
        assert args.no_vad is False

    def test_beam_size_default(self, parser):
        args = parser.parse_args(["video.mp4"])
        assert args.beam_size == 5

    def test_format_default(self, parser):
        args = parser.parse_args(["video.mp4"])
        assert args.format == "srt"

    def test_format_vtt(self, parser):
        args = parser.parse_args(["video.mp4", "--format", "vtt"])
        assert args.format == "vtt"

    def test_format_both(self, parser):
        args = parser.parse_args(["video.mp4", "--format", "both"])
        assert args.format == "both"

    def test_force_default(self, parser):
        args = parser.parse_args(["video.mp4"])
        assert args.force is False

    def test_force_flag(self, parser):
        args = parser.parse_args(["video.mp4", "--force"])
        assert args.force is True


class TestMain:
    def test_no_ffmpeg(self):
        with patch("localsub.cli.check_ffmpeg", return_value=None):
            result = main(["video.mp4"])
            assert result == 1

    def test_file_not_found(self):
        with (
            patch("localsub.cli.check_ffmpeg", return_value="ffmpeg version X"),
        ):
            result = main(["nonexistent.mp4"])
            assert result == 1

    def test_unsupported_format(self, tmp_path):
        bad = tmp_path / "test.txt"
        bad.write_text("not media")
        with (
            patch("localsub.cli.check_ffmpeg", return_value="ffmpeg version X"),
        ):
            result = main([str(bad)])
            assert result == 1

    def test_output_with_multiple_inputs(self):
        with (
            patch("localsub.cli.check_ffmpeg", return_value="ffmpeg version X"),
        ):
            result = main(["a.mp4", "b.mp4", "-o", "out.srt"])
            assert result == 1

    def test_successful_single_file(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.write_text("fake video")
        srt_out = tmp_path / "test.srt"

        with (
            patch("localsub.cli.check_ffmpeg", return_value="ffmpeg version X"),
            patch("localsub.cli.has_audio_stream", return_value=True),
            patch("localsub.cli.process_file", return_value=0),
        ):
            result = main([str(video)])
            assert result == 0

    def test_partial_failure_in_batch(self, tmp_path):
        v1 = tmp_path / "ok.mp4"
        v1.write_text("fake")
        v2 = tmp_path / "bad.mp4"
        # skip writing v2 so it doesn't exist

        with (
            patch("localsub.cli.check_ffmpeg", return_value="ffmpeg version X"),
            patch("localsub.cli.process_file", return_value=0),
        ):
            result = main([str(v1), str(v2)])
            assert result == 1

    def test_version_flag(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["--version"])

    def test_help_flag(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["--help"])


class TestProcessFile:
    def test_no_audio_stream(self, tmp_path):
        video = tmp_path / "silent.mp4"
        video.write_text("fake")

        with (
            patch("localsub.cli.has_audio_stream", return_value=False),
            patch("localsub.cli.check_ffmpeg", return_value="ffmpeg version X"),
        ):
            from localsub.cli import process_file, build_parser
            args = build_parser().parse_args([str(video)])
            result = process_file(video, args)
            assert result == 1

    def test_cache_hit(self, tmp_path):
        video = tmp_path / "test.mp4"
        video.write_text("fake")

        with (
            patch("localsub.cli.has_audio_stream", return_value=True),
            patch("localsub.cli.load_cache", return_value=[
                {"start": 0.0, "end": 1.0, "text": "Hello.", "words": []}
            ]),
            patch("localsub.cli.write_subtitles"),
        ):
            from localsub.cli import process_file, build_parser
            args = build_parser().parse_args([str(video)])
            result = process_file(video, args)
            assert result == 0
