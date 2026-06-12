from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest
from localsub.transcribe import transcribe


class TestTranscribe:
    @patch("localsub.transcribe.WhisperModel")
    def test_transcribe_basic(self, mock_whisper_class):
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model

        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.95
        mock_info.duration = 120.0

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.5
        mock_segment.text = "Hello world."

        mock_model.transcribe.return_value = ([mock_segment], mock_info)

        audio_path = Path("/tmp/test.wav")
        segments, lang = transcribe(audio_path, model_name="base", verbose=True)

        assert lang == "en"
        seg_list = list(segments)
        assert len(seg_list) == 1
        assert seg_list[0].start == 0.0
        assert seg_list[0].text == "Hello world."

        mock_whisper_class.assert_called_once_with(
            "base",
            device="auto",
            compute_type="default",
        )

        _, kwargs = mock_model.transcribe.call_args
        assert kwargs["vad_filter"] is True
        assert kwargs["beam_size"] == 5

    @patch("localsub.transcribe.WhisperModel")
    def test_transcribe_with_options(self, mock_whisper_class):
        mock_model = MagicMock()
        mock_whisper_class.return_value = mock_model

        mock_info = MagicMock()
        mock_info.language = "fr"
        mock_info.duration = 60.0

        mock_model.transcribe.return_value = ([], mock_info)

        segments, lang = transcribe(
            "/tmp/test.wav",
            model_name="large-v3",
            device="cpu",
            compute_type="int8",
            language="fr",
            vad_filter=False,
            beam_size=3,
        )

        assert lang == "fr"

        mock_whisper_class.assert_called_once_with(
            "large-v3",
            device="cpu",
            compute_type="int8",
        )

        _, kwargs = mock_model.transcribe.call_args
        assert kwargs["language"] == "fr"
        assert kwargs["vad_filter"] is False
        assert kwargs["beam_size"] == 3
