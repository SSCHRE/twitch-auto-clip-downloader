import pytest

from download import build_clip_filename, clip_id_suffix, format_clip_timestamp


CLIP = {
    "id": "abcdef123456",
    "title": "Cool Clip",
    "created_at": "2026-01-01T12:00:00Z",
}


def test_format_clip_timestamp():
    assert format_clip_timestamp("2026-01-01T12:00:00Z") == "2026-01-01_12-00-00"


def test_build_clip_filename_title():
    filename = build_clip_filename(
        CLIP,
        clip_name_format="title",
        short_id_length=6,
    )

    assert filename == "Cool Clip_abcdef.%(ext)s"


def test_build_clip_filename_title_allows_duplicate_titles():
    other_clip = {
        **CLIP,
        "id": "ghijkl789012",
        "title": "Cool Clip",
    }

    first = build_clip_filename(
        CLIP,
        clip_name_format="title",
        short_id_length=6,
    )
    second = build_clip_filename(
        other_clip,
        clip_name_format="title",
        short_id_length=6,
    )

    assert first != second
    assert first == "Cool Clip_abcdef.%(ext)s"
    assert second == "Cool Clip_ghijkl.%(ext)s"


def test_build_clip_filename_random():
    filename = build_clip_filename(
        CLIP,
        clip_name_format="random",
        short_id_length=6,
        unique_suffix="randomtoken12",
    )

    assert filename == "clip_randomtoken12.%(ext)s"


def test_build_clip_filename_random_ignores_short_id_length():
    filename = build_clip_filename(
        CLIP,
        clip_name_format="random",
        short_id_length=3,
        unique_suffix="randomtoken12",
    )

    assert filename == "clip_randomtoken12.%(ext)s"
    assert "abc" not in filename


def test_build_clip_filename_random_uses_unique_suffix_for_duplicates():
    first = build_clip_filename(
        CLIP,
        clip_name_format="random",
        short_id_length=6,
        unique_suffix="first-random",
    )
    second = build_clip_filename(
        CLIP,
        clip_name_format="random",
        short_id_length=6,
        unique_suffix="second-random",
    )

    assert first != second
    assert first == "clip_first-random.%(ext)s"
    assert second == "clip_second-random.%(ext)s"


def test_clip_id_suffix_uses_api_suffix_after_hyphen():
    assert clip_id_suffix("CoolClipName-TKUHVRWr8cv8v1pS") == "TKUHVRWr"


def test_clip_id_suffix_truncates_plain_id():
    assert clip_id_suffix("abcdef123456") == "abcdef12"


def test_build_clip_filename_timestamp():
    filename = build_clip_filename(
        CLIP,
        clip_name_format="timestamp",
        short_id_length=6,
    )

    assert filename == "2026-01-01_12-00-00_abcdef12.%(ext)s"


def test_build_clip_filename_timestamp_uses_api_suffix():
    clip = {
        **CLIP,
        "id": "CoolClipName-TKUHVRWr8cv8v1pS",
    }

    filename = build_clip_filename(
        clip,
        clip_name_format="timestamp",
        short_id_length=6,
    )

    assert filename == "2026-01-01_12-00-00_TKUHVRWr.%(ext)s"


def test_build_clip_filename_timestamp_ignores_short_id_length():
    filename = build_clip_filename(
        CLIP,
        clip_name_format="timestamp",
        short_id_length=3,
    )

    assert filename == "2026-01-01_12-00-00_abcdef12.%(ext)s"
    assert "2026-01-01_12-00-00_abc.%(ext)s" != filename


def test_build_clip_filename_timestamp_allows_duplicate_times():
    other_clip = {
        **CLIP,
        "id": "ghijkl789012",
    }

    first = build_clip_filename(
        CLIP,
        clip_name_format="timestamp",
        short_id_length=6,
    )
    second = build_clip_filename(
        other_clip,
        clip_name_format="timestamp",
        short_id_length=6,
    )

    assert first != second
    assert first == "2026-01-01_12-00-00_abcdef12.%(ext)s"
    assert second == "2026-01-01_12-00-00_ghijkl78.%(ext)s"


def test_build_clip_filename_invalid_format():
    with pytest.raises(ValueError, match="Unsupported clip_name_format"):
        build_clip_filename(
            CLIP,
            clip_name_format="invalid",
            short_id_length=6,
        )
