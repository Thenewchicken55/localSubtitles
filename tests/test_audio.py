import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from localsub.audio import check_ffmpeg, extract_audio


class TestCheckFfmpeg:
    @patch("localsub.audio.subprocess.run")
    def test_ffmpeg_found(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "ffmpeg version 5.1.3 Copyright (c) 2000-2023 the FFmpeg developers\n"
        result = check_ffmpeg()
        assert result is not None
        assert "ffmpeg version" in result

    @patch("localsub.audio.subprocess.run")
    def test_ffmpeg_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        result = check_ffmpeg()
        assert result is None

    @patch("localsub.audio.subprocess.run")
    def test_ffmpeg_nonzero_exit(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        result = check_ffmpeg()
        assert result is None

    @patch("localsub.audio.subprocess.run")
    def test_ffmpeg_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=10)
        result = check_ffmpeg()
        assert result is None


class TestExtractAudio:
    @patch("localsub.audio.subprocess.run")
    def test_successful_extraction(self, mock_run, tmp_path):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        input_path = tmp_path / "input.mp4"
        input_path.write_text("fake")
        output_path = tmp_path / "output.wav"
        output_path.write_text("fake wav")

        result = extract_audio(input_path, output_path)
        assert result == output_path

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args
        assert "-ar" in args
        assert "16000" in args
        assert "-ac" in args
        assert "1" in args

    @patch("localsub.audio.subprocess.run")
    def test_output_not_created(self, mock_run, tmp_path):
        mock_run.return_value.returncode = 0
        input_path = tmp_path / "input.mp4"
        input_path.write_text("fake")
        output_path = tmp_path / "nonexistent.wav"

        with pytest.raises(RuntimeError, match="output file not found"):
            extract_audio(input_path, output_path)

    def test_ffmpeg_not_installed(self, tmp_path):
        input_path = tmp_path / "input.mp4"
        input_path.write_text("fake")
        output_path = tmp_path / "output.wav"

        with patch("localsub.audio.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with pytest.raises(RuntimeError, match="ffmpeg not found"):
                extract_audio(input_path, output_path)

    @patch("localsub.audio.subprocess.run")
    def test_ffmpeg_failure(self, mock_run, tmp_path):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Invalid data found"
        input_path = tmp_path / "input.mp4"
        input_path.write_text("fake")
        output_path = tmp_path / "output.wav"

        with pytest.raises(RuntimeError, match="ffmpeg failed"):
            extract_audio(input_path, output_path)
