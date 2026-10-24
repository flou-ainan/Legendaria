import pytest

from legendaria_engine.formats import format_timestamp, to_srt, to_vtt


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00:00,000"),
        (59.999, "00:00:59,999"),
        (59.9996, "00:01:00,000"),
        (61.5, "00:01:01,500"),
        (3725.042, "01:02:05,042"),
        (90000, "25:00:00,000"),
        (-1, "00:00:00,000"),
    ],
)
def test_format_timestamp_srt(seconds, expected):
    assert format_timestamp(seconds) == expected


def test_format_timestamp_vtt_separator():
    assert format_timestamp(1.25, ".") == "00:00:01.250"


def test_to_srt(transcript):
    assert to_srt(transcript) == (
        "1\n00:00:00,000 --> 00:00:02,500\nOlá, este é um teste.\n\n"
        "2\n01:02:03,000 --> 01:02:05,500\nHello again.\n"
    )


def test_to_vtt(transcript):
    text = to_vtt(transcript)
    assert text.startswith("WEBVTT\n\n00:00:00.000 --> 00:00:02.500\nOlá, este é um teste.\n")
    assert "01:02:03.000 --> 01:02:05.500\nHello again.\n" in text
