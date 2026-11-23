import pytest

import app


def run_once(*, rclone_result, pending_clips, calls, cleanup=True):
    def fake_sleep(seconds):
        raise KeyboardInterrupt

    def fake_rclone():
        calls.append("rclone")
        return rclone_result

    with pytest.raises(KeyboardInterrupt):
        app.run(
            channels=["testchannel"],
            interval=60,
            enable_rclone=True,
            enable_vod_download=True,
            cleanup_uploaded_files=(
                (lambda: calls.append("cleanup")) if cleanup else None
            ),
            initialize=lambda: None,
            get_user_id=lambda channel: "123",
            get_clips=lambda uid: [],
            download_clip=lambda clip, channel: True,
            run_rclone=fake_rclone,
            has_clip=lambda clip_id: False,
            save_clip=lambda *args: None,
            get_unuploaded_clips=lambda: pending_clips,
            mark_all_uploaded=lambda: calls.append("mark"),
            get_videos=lambda uid: [],
            download_vod=lambda video, channel: True,
            has_vod=lambda vod_id: False,
            save_vod=lambda *args: None,
            get_unuploaded_vods=lambda: [],
            mark_all_vods_uploaded=lambda: None,
            sleep=fake_sleep,
        )


def test_cleanup_runs_after_successful_upload():
    calls = []
    run_once(rclone_result=True, pending_clips=["clip1"], calls=calls)
    assert calls == ["rclone", "mark", "cleanup"]


def test_cleanup_skipped_when_upload_fails():
    calls = []
    run_once(rclone_result=False, pending_clips=["clip1"], calls=calls)
    assert calls == ["rclone"]


def test_cleanup_skipped_when_nothing_uploaded():
    calls = []
    run_once(rclone_result=True, pending_clips=[], calls=calls)
    assert calls == []


def test_no_cleanup_when_not_provided():
    calls = []
    run_once(
        rclone_result=True,
        pending_clips=["clip1"],
        calls=calls,
        cleanup=False,
    )
    assert calls == ["rclone", "mark"]
