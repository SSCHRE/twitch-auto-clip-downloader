from unittest.mock import Mock
import bot
import json
import importlib


def load_bot_with_config(monkeypatch, tmp_path, config_data):
    """
    Helper that creates a temporary config.json
    """

    config_file = tmp_path / "config.json"

    config_file.write_text(
        json.dumps(config_data)
    )

    monkeypatch.chdir(tmp_path)

    import bot

    return importlib.reload(bot)


def test_download_clip_builds_title_filename(monkeypatch, tmp_path):
    captured = {}

    fake_result = Mock()
    fake_result.returncode = 0

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return fake_result

    monkeypatch.setattr(bot.subprocess, "run", fake_run)
    monkeypatch.setattr(bot, "get_game_name", lambda x: "Minecraft")
    monkeypatch.setattr(bot, "CLIP_NAME_FORMAT", "title")

    clip = {
        "id": "abcdef123456",
        "url": "https://twitch.tv/clip/test",
        "title": "Cool Clip",
        "game_id": "123",
        "created_at": "2026-01-01T12:00:00Z",
    }

    result = bot.download_clip(clip, "testchannel")

    assert result is True
    assert "Cool Clip_abcdef.%(ext)s" in captured["cmd"][5]


def test_download_clip_builds_timestamp_filename(monkeypatch, tmp_path):
    captured = {}

    fake_result = Mock()
    fake_result.returncode = 0

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda cmd, **kwargs: captured.update({"cmd": cmd}) or fake_result,
    )
    monkeypatch.setattr(bot, "get_game_name", lambda x: "Minecraft")
    monkeypatch.setattr(bot, "CLIP_NAME_FORMAT", "timestamp")

    clip = {
        "id": "abcdef123456",
        "url": "https://twitch.tv/clip/test",
        "title": "Cool Clip",
        "game_id": "123",
        "created_at": "2026-01-01T12:00:00Z",
    }

    bot.download_clip(clip, "testchannel")

    assert "2026-01-01_12-00-00_abcdef12.%(ext)s" in captured["cmd"][5]


def test_download_clip_builds_random_filename(monkeypatch, tmp_path):
    captured = {}

    fake_result = Mock()
    fake_result.returncode = 0

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda cmd, **kwargs: captured.update({"cmd": cmd}) or fake_result,
    )
    monkeypatch.setattr(bot, "get_game_name", lambda x: "Minecraft")
    monkeypatch.setattr(bot, "CLIP_NAME_FORMAT", "random")

    import download

    monkeypatch.setattr(
        download.uuid,
        "uuid4",
        lambda: type("UUID", (), {"hex": "fixedrandom123"})(),
    )

    clip = {
        "id": "abcdef123456",
        "url": "https://twitch.tv/clip/test",
        "title": "Cool Clip",
        "game_id": "123",
        "created_at": "2026-01-01T12:00:00Z",
    }

    bot.download_clip(clip, "testchannel")

    assert "clip_fixedrandom1.%(ext)s" in captured["cmd"][5]


def test_default_clip_name_format(monkeypatch, tmp_path):
    config_data = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
    }

    loaded_bot = load_bot_with_config(monkeypatch, tmp_path, config_data)

    assert loaded_bot.CLIP_NAME_FORMAT == "title"


def test_custom_clip_name_format(monkeypatch, tmp_path):
    config_data = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
        "clip_name_format": "timestamp",
    }

    loaded_bot = load_bot_with_config(monkeypatch, tmp_path, config_data)

    assert loaded_bot.CLIP_NAME_FORMAT == "timestamp"


def test_default_clip_folder_order(monkeypatch, tmp_path):
    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"]
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.CLIP_FOLDER_ORDER == "game_date"

def test_custom_clip_folder_order(monkeypatch, tmp_path):
    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
        "clip_folder_order": "date_game"
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.CLIP_FOLDER_ORDER == "date_game"