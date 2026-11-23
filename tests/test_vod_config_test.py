import pytest

import config


def test_invalid_enable_vod_download_type():
    with pytest.raises(ValueError, match="enable_vod_download"):
        config.validate_general_config(
            "id",
            "secret",
            60,
            6,
            ["channel"],
            "game_date",
            "title",
            1,
            "yes",
            7,
            "title",
        )


def test_invalid_vod_lookback_days():
    with pytest.raises(ValueError, match="vod_lookback_days"):
        config.validate_general_config(
            "id",
            "secret",
            60,
            6,
            ["channel"],
            "game_date",
            "title",
            1,
            True,
            0,
            "title",
        )


def test_invalid_vod_name_format():
    with pytest.raises(ValueError, match="vod_name_format"):
        config.validate_general_config(
            "id",
            "secret",
            60,
            6,
            ["channel"],
            "game_date",
            "title",
            1,
            True,
            7,
            "invalid",
        )


def test_vod_download_enabled_logs_info(caplog):
    caplog.set_level("INFO")

    config.validate_general_config(
        "id",
        "secret",
        60,
        6,
        ["channel"],
        "game_date",
        "title",
        1,
        True,
        7,
        "title",
    )

    assert "VOD download enabled" in caplog.text
