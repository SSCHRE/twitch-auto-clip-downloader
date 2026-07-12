from unittest.mock import Mock
import bot

def test_rclone_success(monkeypatch):
    fake_result = Mock()
    fake_result.returncode = 0

    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda *args, **kwargs: fake_result
    )

    assert bot.run_rclone() is True


def test_rclone_failure(monkeypatch):
    fake_result = Mock()
    fake_result.returncode = 1

    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        lambda *args, **kwargs: fake_result
    )

    assert bot.run_rclone() is False


def test_rclone_missing(monkeypatch):
    monkeypatch.setattr(
        bot,
        "ENABLE_RCLONE",
        True
    )

    def fake_run(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(
        bot.subprocess,
        "run",
        fake_run
    )

    assert bot.run_rclone() is False