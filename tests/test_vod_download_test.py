from unittest.mock import Mock

import bot
import download


def test_download_vod_builds_title_filename(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.chdir(tmp_path)

    fake_result = Mock()
    fake_result.returncode = 0

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda cmd, **kwargs: captured.update({"cmd": cmd}) or fake_result,
    )
    monkeypatch.setattr(bot, "VOD_NAME_FORMAT", "title")
    monkeypatch.setattr(bot, "VERIFY_DOWNLOADS", False)

    video = {
        "id": "335921245",
        "url": "https://www.twitch.tv/videos/335921245",
        "title": "Cool Stream",
        "published_at": "2026-01-01T12:00:00Z",
        "created_at": "2026-01-01T12:00:00Z",
    }

    result = bot.download_vod(video, "testchannel")

    assert result is True
    assert "Cool Stream_335921.%(ext)s" in captured["cmd"][5]
    assert "vods" in captured["cmd"][5]


def test_download_vod_builds_timestamp_filename(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.chdir(tmp_path)

    fake_result = Mock()
    fake_result.returncode = 0

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda cmd, **kwargs: captured.update({"cmd": cmd}) or fake_result,
    )
    monkeypatch.setattr(bot, "VOD_NAME_FORMAT", "timestamp")

    video = {
        "id": "335921245",
        "url": "https://www.twitch.tv/videos/335921245",
        "title": "Cool Stream",
        "published_at": "2026-01-01T12:00:00Z",
        "created_at": "2026-01-01T12:00:00Z",
    }

    bot.download_vod(video, "testchannel")

    assert "2026-01-01_12-00-00_33592124.%(ext)s" in captured["cmd"][5]


def test_build_vod_filename_random():
    video = {
        "id": "335921245",
        "title": "Cool Stream",
        "published_at": "2026-01-01T12:00:00Z",
        "created_at": "2026-01-01T12:00:00Z",
    }

    filename = download.build_vod_filename(
        video,
        vod_name_format="random",
        short_id_length=6,
        unique_suffix="abcdef123456",
    )

    assert filename == "vod_abcdef123456.%(ext)s"
