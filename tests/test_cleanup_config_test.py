import pytest

import config


def test_rejects_sync_when_cleanup_enabled():
    with pytest.raises(ValueError, match="rclone_command.*copy"):
        config.validate_rclone_config(
            True,
            ["gdrive"],
            "sync",
            [],
            "TwitchClips",
            False,
            delete_local_clips_outside_lookback=True,
        )


def test_rejects_move_when_cleanup_enabled():
    with pytest.raises(ValueError, match="rclone_command.*copy"):
        config.validate_rclone_config(
            True,
            ["gdrive"],
            "move",
            [],
            "TwitchClips",
            False,
            delete_local_clips_outside_lookback=True,
        )


def test_allows_copy_when_cleanup_enabled(caplog):
    caplog.set_level("INFO")

    config.validate_rclone_config(
        True,
        ["gdrive"],
        "copy",
        [],
        "TwitchClips",
        False,
        delete_local_clips_outside_lookback=True,
    )

    assert "rclone copy is required" in caplog.text


def test_cleanup_without_rclone_does_not_require_copy():
    config.validate_rclone_config(
        False,
        [],
        "sync",
        [],
        "TwitchClips",
        False,
        delete_local_clips_outside_lookback=True,
    )
