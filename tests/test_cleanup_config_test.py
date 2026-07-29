import pytest

import config


@pytest.fixture
def rclone_on_path(monkeypatch):
    monkeypatch.setattr(
        config,
        "find_rclone_executable",
        lambda: "/usr/bin/rclone",
    )


def test_rejects_sync_when_cleanup_enabled(rclone_on_path):
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


def test_rejects_move_when_cleanup_enabled(rclone_on_path):
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


def test_allows_copy_when_cleanup_enabled(rclone_on_path, caplog):
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
