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

def test_download_clip_builds_command(monkeypatch, tmp_path):
    fake_result = Mock()
    fake_result.returncode = 0

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda *args, **kwargs: fake_result
    )

    monkeypatch.setattr(
        bot,
        "get_game_name",
        lambda x: "Minecraft"
    )

    clip = {
        "id": "abcdef123456",
        "url": "https://twitch.tv/clip/test",
        "title": "Cool Clip",
        "game_id": "123",
        "created_at": "2026-01-01T12:00:00Z"
    }

    result = bot.download_clip(
        clip,
        "testchannel"
    )

    assert result is True

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