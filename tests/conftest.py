from pathlib import Path
import pytest


@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    p = tmp_path / "test_video.mp4"
    p.write_text("fake video content")
    return p


@pytest.fixture
def sample_audio_path(tmp_path: Path) -> Path:
    p = tmp_path / "test_audio.mp3"
    p.write_text("fake audio content")
    return p


@pytest.fixture
def unsupported_path(tmp_path: Path) -> Path:
    p = tmp_path / "test.txt"
    p.write_text("not media")
    return p


@pytest.fixture
def sample_segments():
    class FakeSegment:
        def __init__(self, start, end, text):
            self.start = start
            self.end = end
            self.text = text

    return [
        FakeSegment(0.0, 2.5, "Hello world."),
        FakeSegment(2.5, 5.0, "This is a test of the subtitle generation system."),
        FakeSegment(5.0, 7.3, "It should handle punctuation and line wrapping correctly."),
    ]
