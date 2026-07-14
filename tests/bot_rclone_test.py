from unittest.mock import Mock
import bot

def test_rclone_disabled(monkeypatch):
    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        False
    )

    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        fake_run
    )

    assert bot.run_rclone() is True
    assert called is False


def test_rclone_single_remote_success(monkeypatch):
    fake_result = Mock()
    fake_result.returncode = 0

    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    monkeypatch.setattr(
        bot,
        "RCLONE_REMOTES",
        [
            "gdrive"
        ]
    )

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda *args, **kwargs: fake_result
    )

    assert bot.run_rclone() is True


def test_rclone_multiple_remotes(monkeypatch):
    fake_result = Mock()
    fake_result.returncode = 0

    calls = []

    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    monkeypatch.setattr(
        bot,
        "RCLONE_REMOTES",
        [
            "gdrive",
            "onedrive"
        ]
    )

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return fake_result

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        fake_run
    )

    assert bot.run_rclone() is True

    assert len(calls) == 2

    assert calls[0] == [
        "rclone",
        "copy",
        "clips",
        "gdrive:TwitchClips"
    ]

    assert calls[1] == [
        "rclone",
        "copy",
        "clips",
        "onedrive:TwitchClips"
    ]


def test_rclone_one_remote_fails(monkeypatch):
    calls = 0

    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    monkeypatch.setattr(
        bot,
        "RCLONE_REMOTES",
        [
            "gdrive",
            "onedrive"
        ]
    )

    def fake_run(*args, **kwargs):
        nonlocal calls

        result = Mock()

        if calls == 0:
            result.returncode = 0
        else:
            result.returncode = 1

        calls += 1

        return result

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        fake_run
    )

    assert bot.run_rclone() is False


def test_rclone_missing(monkeypatch):
    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    monkeypatch.setattr(
        bot,
        "RCLONE_REMOTES",
        [
            "gdrive"
        ]
    )

    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        fake_run
    )

    assert bot.run_rclone() is False

def test_rclone_progress_enabled(monkeypatch):
    fake_result = Mock()
    fake_result.returncode = 0

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
        bot,
        "RCLONE_SHOW_PROGRESS",
        True
    )

    captured = {}

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        return fake_result

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        fake_run
    )

    assert bot.run_rclone() is True

    assert captured["stdout"] is None
    assert captured["stderr"] is None