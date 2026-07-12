import pytest
import bot

def test_interval_too_low(monkeypatch):
    monkeypatch.setattr(
        bot,
        "INTERVAL",
        10
    )

    with pytest.raises(ValueError):
        bot.validate_config()


def test_short_id_length_zero(monkeypatch):
    monkeypatch.setattr(
        bot,
        "SHORT_ID_LENGTH",
        0
    )

    with pytest.raises(ValueError):
        bot.validate_config()


def test_channels_empty(monkeypatch):
    monkeypatch.setattr(
        bot,
        "CHANNELS",
        []
    )

    with pytest.raises(ValueError):
        bot.validate_config()


def test_channels_must_be_list(monkeypatch):
    monkeypatch.setattr(
        bot,
        "CHANNELS",
        "not-a-list"
    )

    with pytest.raises(ValueError):
        bot.validate_config()


def test_valid_config(monkeypatch):
    monkeypatch.setattr(
        bot,
        "INTERVAL",
        60
    )

    monkeypatch.setattr(
        bot,
        "SHORT_ID_LENGTH",
        6
    )

    monkeypatch.setattr(
        bot,
        "CHANNELS",
        ["channel1"]
    )

    bot.validate_config()

def test_default_rclone_destination(monkeypatch, tmp_path):
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

    assert bot.RCLONE_DESTINATION == "TwitchClips"

def test_custom_rclone_destination(monkeypatch, tmp_path):
    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
        "rclone_destination": "Backups/Twitch"
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.RCLONE_DESTINATION == "Backups/Twitch"