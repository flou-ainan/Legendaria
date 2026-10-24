import pytest
from conftest import load

timecode = load("timecode")


@pytest.mark.parametrize(
    ("seconds", "fps", "offset", "frame"),
    [(0, 24, 1, 1), (1.0, 24, 1, 25), (0.52, 25, 10, 23), (2.0, 29.97, 0, 60)],
)
def test_seconds_to_frame(seconds, fps, offset, frame):
    assert timecode.seconds_to_frame(seconds, fps, offset) == frame


def test_frame_round_trip():
    assert timecode.frame_to_seconds(timecode.seconds_to_frame(3.5, 24, 1), 24, 1) == 3.5


def test_timestamps_match_engine_format():
    assert timecode.format_timestamp(3725.042) == "01:02:05,042"
    assert timecode.format_timestamp(1.25, ".") == "00:00:01.250"


def test_srt_and_vtt():
    cues = [(0.0, 1.5, "Olá"), (2.0, 3.0, " mundo ")]
    assert timecode.to_srt(cues) == (
        "1\n00:00:00,000 --> 00:00:01,500\nOlá\n\n2\n00:00:02,000 --> 00:00:03,000\nmundo\n"
    )
    assert timecode.to_vtt(cues).startswith("WEBVTT\n\n00:00:00.000 --> 00:00:01.500\nOlá\n")
