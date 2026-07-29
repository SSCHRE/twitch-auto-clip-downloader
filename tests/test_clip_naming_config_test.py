import pytest

import config


VALID_CONFIG = (
    "id",
    "secret",
    60,
    6,
    ["channel"],
    "game_date",
    "title",
    1,
    False,
)


def test_invalid_clip_name_format():
    with pytest.raises(ValueError, match="clip_name_format"):
        config.validate_general_config(
            "id",
            "secret",
            60,
            6,
            ["channel"],
            "game_date",
            "invalid",
            1,
            False,
        )


@pytest.mark.parametrize("clip_name_format", ["random", "timestamp"])
def test_logs_short_id_length_ignored_when_not_title(caplog, clip_name_format):
    caplog.set_level("INFO")

    config.validate_general_config(
        *VALID_CONFIG[:6],
        clip_name_format,
        VALID_CONFIG[7],
        VALID_CONFIG[8],
    )

    assert "short_id_length is ignored" in caplog.text
    assert clip_name_format in caplog.text


def test_does_not_log_short_id_length_ignored_for_title(caplog):
    caplog.set_level("INFO")

    config.validate_general_config(*VALID_CONFIG)

    assert "short_id_length is ignored" not in caplog.text

