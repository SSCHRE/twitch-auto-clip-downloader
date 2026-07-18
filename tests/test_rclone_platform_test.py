import pytest

import config

RCLONE_PATHS = [
    pytest.param("/usr/bin/rclone", id="linux"),
    pytest.param("/opt/homebrew/bin/rclone", id="macos-homebrew"),
    pytest.param("/usr/local/bin/rclone", id="macos-local"),
    pytest.param(r"C:\Program Files\rclone\rclone.exe", id="windows"),
]


@pytest.mark.parametrize("resolved_path", RCLONE_PATHS)
def test_find_rclone_executable_resolves_on_all_platforms(
    monkeypatch,
    resolved_path,
):
    monkeypatch.setattr(
        config.shutil,
        "which",
        lambda name: resolved_path if name == "rclone" else None,
    )

    assert config.find_rclone_executable() == resolved_path


@pytest.mark.parametrize("resolved_path", RCLONE_PATHS)
def test_rclone_validation_passes_when_executable_found(
    monkeypatch,
    resolved_path,
):
    monkeypatch.setattr(
        config.shutil,
        "which",
        lambda name: resolved_path if name == "rclone" else None,
    )

    config.validate_rclone_config(
        enable_rclone=True,
        rclone_remotes=["gdrive"],
        rclone_command="copy",
        rclone_args=[],
        rclone_destination="TwitchClips",
        rclone_show_progress=False,
    )


def test_rclone_validation_fails_when_executable_missing(monkeypatch):
    monkeypatch.setattr(
        config.shutil,
        "which",
        lambda name: None,
    )

    with pytest.raises(ValueError, match="rclone"):
        config.validate_rclone_config(
            enable_rclone=True,
            rclone_remotes=["gdrive"],
            rclone_command="copy",
            rclone_args=[],
            rclone_destination="TwitchClips",
            rclone_show_progress=False,
        )


def test_find_rclone_executable_looks_up_rclone_command(monkeypatch):
    seen = []

    def fake_which(name):
        seen.append(name)
        return "/usr/bin/rclone"

    monkeypatch.setattr(config.shutil, "which", fake_which)

    config.find_rclone_executable()

    assert seen == ["rclone"]
