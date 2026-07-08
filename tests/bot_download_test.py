from unittest.mock import Mock
import bot

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