import pytest
import json
import importlib

def test_missing_client_id(monkeypatch, tmp_path):
    config = {
        "client_secret": "secret",
        "channels": ["testchannel"]
    }

    with pytest.raises(KeyError):
        load_bot_with_config(
            monkeypatch,
            tmp_path,
            config
        )


def test_missing_client_secret(monkeypatch, tmp_path):
    config = {
        "client_id": "id",
        "channels": ["testchannel"]
    }

    with pytest.raises(KeyError):
        load_bot_with_config(
            monkeypatch,
            tmp_path,
            config
        )


def test_missing_channels_fails(monkeypatch, tmp_path):

    config = {
        "client_id": "id",
        "client_secret": "secret"
    }

    with pytest.raises(ValueError, match="channels"):
        load_bot_with_config(
            monkeypatch,
            tmp_path,
            config
        )

    config = {
        "client_id": "id",
        "client_secret": "secret"
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.CHANNELS == []

def test_missing_channels_fails(monkeypatch, tmp_path):

    config = {
        "client_id": "id",
        "client_secret": "secret"
    }

    with pytest.raises(ValueError, match="channels"):
        load_bot_with_config(
            monkeypatch,
            tmp_path,
            config
        )

def test_custom_interval(monkeypatch, tmp_path):
    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
        "check_interval_seconds": 120
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.INTERVAL == 120


def test_default_short_id_length(monkeypatch, tmp_path):
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

    assert bot.SHORT_ID_LENGTH == 6

def test_channels_must_be_list(monkeypatch, tmp_path):

    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": "testchannel"
    }

    with pytest.raises(ValueError, match="channels"):
        load_bot_with_config(
            monkeypatch,
            tmp_path,
            config
        )
        
def test_custom_short_id_length(monkeypatch, tmp_path):
    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
        "short_id_length": 10
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.SHORT_ID_LENGTH == 10


def test_default_yt_dlp_quiet(monkeypatch, tmp_path):
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

    assert bot.YT_DLP_QUIET is False


def test_enable_yt_dlp_quiet(monkeypatch, tmp_path):
    config = {
        "client_id": "id",
        "client_secret": "secret",
        "channels": ["testchannel"],
        "yt_dlp_quiet": True
    }

    bot = load_bot_with_config(
        monkeypatch,
        tmp_path,
        config
    )

    assert bot.YT_DLP_QUIET is True