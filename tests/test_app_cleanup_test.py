import pytest

import app


def test_run_calls_cleanup_after_rclone():
    calls = []

    def fake_sleep(seconds):
        raise KeyboardInterrupt

    def fake_cleanup():
        calls.append("cleanup")

    def fake_rclone():
        calls.append("rclone")
        return True

    with pytest.raises(KeyboardInterrupt):
        app.run(
            channels=["testchannel"],
            interval=60,
            enable_rclone=True,
            cleanup_local_clips=fake_cleanup,
            initialize=lambda: None,
            get_user_id=lambda channel: "123",
            get_clips=lambda uid: [],
            download_clip=lambda clip, channel: True,
            run_rclone=fake_rclone,
            has_clip=lambda clip_id: False,
            save_clip=lambda *args: None,
            get_unuploaded_clips=lambda: ["clip1"],
            mark_all_uploaded=lambda: None,
            sleep=fake_sleep,
        )

    assert calls == ["rclone", "cleanup"]


def test_run_skips_cleanup_when_not_provided():
    calls = []

    def fake_sleep(seconds):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        app.run(
            channels=["testchannel"],
            interval=60,
            enable_rclone=False,
            cleanup_local_clips=None,
            initialize=lambda: None,
            get_user_id=lambda channel: "123",
            get_clips=lambda uid: [],
            download_clip=lambda clip, channel: True,
            run_rclone=lambda: True,
            has_clip=lambda clip_id: False,
            save_clip=lambda *args: None,
            get_unuploaded_clips=lambda: [],
            mark_all_uploaded=lambda: None,
            sleep=fake_sleep,
        )

    assert calls == []
