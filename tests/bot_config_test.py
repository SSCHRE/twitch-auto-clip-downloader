import pytest
import bot

def test_empty_client_id(monkeypatch):
    monkeypatch.setattr(
        bot,
        "CLIENT_ID",
        ""
    )

    with pytest.raises(ValueError, match="client_id"):
        bot.validate_config()


def test_whitespace_client_id(monkeypatch):
    monkeypatch.setattr(
        bot,
        "CLIENT_ID",
        "   "
    )

    with pytest.raises(ValueError, match="client_id"):
        bot.validate_config()


def test_empty_client_secret(monkeypatch):
    monkeypatch.setattr(
        bot,
        "CLIENT_SECRET",
        ""
    )

    with pytest.raises(ValueError, match="client_secret"):
        bot.validate_config()


def test_whitespace_client_secret(monkeypatch):
    monkeypatch.setattr(
        bot,
        "CLIENT_SECRET",
        "   "
    )

    with pytest.raises(ValueError, match="client_secret"):
        bot.validate_config()


def test_rclone_not_on_path_when_enabled(monkeypatch):
    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    monkeypatch.setattr(
        bot,
        "RCLONE_REMOTES",
        ["gdrive"]
    )

    monkeypatch.setattr(
        "config.shutil.which",
        lambda cmd: None
    )

    with pytest.raises(ValueError, match="rclone"):
        bot.validate_config()


def test_rclone_not_checked_when_disabled(monkeypatch):
    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        False
    )

    monkeypatch.setattr(
        "config.shutil.which",
        lambda cmd: None
    )

    bot.validate_config()


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

def test_default_clip_lookback_days(monkeypatch, tmp_path):

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

    assert bot.CLIP_LOOKBACK_DAYS == 1


def test_custom_clip_lookback_days(monkeypatch, tmp_path):

    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
        "clip_lookback_days": 14
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.CLIP_LOOKBACK_DAYS == 14