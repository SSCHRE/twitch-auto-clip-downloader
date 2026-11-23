import pytest

import config


@pytest.fixture
def rclone_on_path(monkeypatch):
    monkeypatch.setattr(
        config,
        "find_rclone_executable",
        lambda: "/usr/bin/rclone",
    )


@pytest.mark.parametrize("command", ["sync", "move"])
def test_rejects_non_copy_when_cleanup_enabled(rclone_on_path, command):
    with pytest.raises(ValueError, match="rclone_command.*copy"):
        config.validate_rclone_config(
            True,
            ["gdrive"],
            command,
            [],
            "TwitchClips",
            False,
            delete_local_after_upload=True,
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
        delete_local_after_upload=True,
    )

    assert "deleted after a successful rclone upload" in caplog.text


def test_cleanup_without_rclone_warns(caplog):
    config.validate_rclone_config(
        False,
        [],
        "sync",
        [],
        "TwitchClips",
        False,
        delete_local_after_upload=True,
    )

    assert "has no effect" in caplog.text


def test_rejects_non_bool_cleanup():
    with pytest.raises(ValueError, match="delete_local_after_upload"):
        config.validate_rclone_config(
            False,
            [],
            "copy",
            [],
            "TwitchClips",
            False,
            delete_local_after_upload="yes",
        )
