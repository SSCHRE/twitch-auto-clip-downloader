import pytest

import app


def test_run_downloads_new_vod_and_skips_existing():
    saved = []
    downloaded = []

    def fake_sleep(seconds):
        raise KeyboardInterrupt

    videos = [
        {
            "id": "vod-1",
            "title": "First",
            "url": "https://www.twitch.tv/videos/1",
            "published_at": "2026-01-01T12:00:00Z",
        },
        {
            "id": "vod-2",
            "title": "Second",
            "url": "https://www.twitch.tv/videos/2",
            "published_at": "2026-01-02T12:00:00Z",
        },
    ]

    with pytest.raises(KeyboardInterrupt):
        app.run(
            channels=["testchannel"],
            interval=60,
            enable_rclone=False,
            enable_vod_download=True,
            initialize=lambda: None,
            get_user_id=lambda channel: "123",
            get_clips=lambda uid: [],
            download_clip=lambda clip, channel: True,
            run_rclone=lambda: True,
            has_clip=lambda clip_id: False,
            save_clip=lambda *args: None,
            get_unuploaded_clips=lambda: [],
            mark_all_uploaded=lambda: None,
            get_videos=lambda uid: videos,
            download_vod=lambda video, channel: downloaded.append(video["id"])
            or True,
            has_vod=lambda vod_id: vod_id == "vod-1",
            save_vod=lambda *args: saved.append(args[0]),
            get_unuploaded_vods=lambda: [],
            mark_all_vods_uploaded=lambda: None,
            sleep=fake_sleep,
        )

    assert downloaded == ["vod-2"]
    assert saved == ["vod-2"]


def test_run_skips_vods_when_disabled():
    called = []

    def fake_sleep(seconds):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        app.run(
            channels=["testchannel"],
            interval=60,
            enable_rclone=False,
            enable_vod_download=False,
            initialize=lambda: None,
            get_user_id=lambda channel: "123",
            get_clips=lambda uid: [],
            download_clip=lambda clip, channel: True,
            run_rclone=lambda: True,
            has_clip=lambda clip_id: False,
            save_clip=lambda *args: None,
            get_unuploaded_clips=lambda: [],
            mark_all_uploaded=lambda: None,
            get_videos=lambda uid: called.append("get_videos") or [],
            download_vod=lambda video, channel: True,
            has_vod=lambda vod_id: False,
            save_vod=lambda *args: None,
            sleep=fake_sleep,
        )

    assert called == []
