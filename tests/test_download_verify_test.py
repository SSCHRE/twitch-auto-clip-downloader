import shutil
import subprocess
from unittest.mock import Mock

import pytest

import download


def test_parse_twitch_duration():
    assert download.parse_twitch_duration(29.9) == 29.9
    assert download.parse_twitch_duration("1h2m3s") == 3723
    assert download.parse_twitch_duration("45m") == 2700
    assert download.parse_twitch_duration("12s") == 12
    assert download.parse_twitch_duration("") is None
    assert download.parse_twitch_duration(None) is None
    assert download.parse_twitch_duration("garbage") is None


def fake_ffprobe(returncode, stdout):
    result = Mock()
    result.returncode = returncode
    result.stdout = stdout
    module = Mock()
    module.run = lambda *args, **kwargs: result
    return module


def test_complete_media_accepts_full_length():
    module = fake_ffprobe(0, "29.5\n")
    assert download.is_complete_media("f.mp4", 30, subprocess_module=module)


def test_complete_media_rejects_truncated():
    module = fake_ffprobe(0, "10.0\n")
    assert not download.is_complete_media(
        "f.mp4", 30, subprocess_module=module
    )


def test_complete_media_rejects_unreadable():
    module = fake_ffprobe(1, "")
    assert not download.is_complete_media(
        "f.mp4", 30, subprocess_module=module
    )


def test_complete_media_without_expected_duration():
    module = fake_ffprobe(0, "5.0\n")
    assert download.is_complete_media("f.mp4", None, subprocess_module=module)


def test_verify_download_deletes_broken_file(tmp_path):
    (tmp_path / "Cool Clip_abcdef.mp4").write_text("broken")
    (tmp_path / "Other_123456.mp4").write_text("keep")

    ok = download.verify_download(
        str(tmp_path),
        "Cool Clip_abcdef.%(ext)s",
        30,
        lambda path, expected: False,
    )

    assert ok is False
    assert not (tmp_path / "Cool Clip_abcdef.mp4").exists()
    assert (tmp_path / "Other_123456.mp4").exists()


def test_verify_download_keeps_good_file(tmp_path):
    (tmp_path / "Cool Clip_abcdef.mp4").write_text("good")

    ok = download.verify_download(
        str(tmp_path),
        "Cool Clip_abcdef.%(ext)s",
        30,
        lambda path, expected: True,
    )

    assert ok is True
    assert (tmp_path / "Cool Clip_abcdef.mp4").exists()


def test_verify_download_fails_when_no_file(tmp_path):
    (tmp_path / "Cool Clip_abcdef.mp4.part").write_text("partial")

    ok = download.verify_download(
        str(tmp_path),
        "Cool Clip_abcdef.%(ext)s",
        30,
        lambda path, expected: True,
    )

    assert ok is False


def test_download_clip_rejects_broken_download(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def fake_ytdlp(cmd, **kwargs):
        # simulate yt-dlp exiting 0 but leaving a broken file
        output = cmd[cmd.index("-o") + 1].replace("%(ext)s", "mp4")
        with open(output, "w") as f:
            f.write("broken")
        result = Mock()
        result.returncode = 0
        return result

    module = Mock()
    module.run = fake_ytdlp
    module.DEVNULL = None

    clip = {
        "id": "abcdef123456",
        "url": "https://twitch.tv/clip/test",
        "title": "Cool Clip",
        "game_id": "1",
        "created_at": "2026-01-01T12:00:00Z",
        "duration": 30.0,
    }

    ok = download.download_clip(
        clip,
        "testchannel",
        short_id_length=6,
        clip_folder_order="game_date",
        clip_name_format="title",
        yt_dlp_quiet=True,
        show_progress=False,
        get_game_name=lambda game_id: "Game",
        subprocess_module=module,
        verify_file=lambda path, expected: False,
    )

    assert ok is False
    folder = tmp_path / "clips" / "testchannel" / "Game" / "2026-01-01"
    assert list(folder.iterdir()) == []


needs_ffmpeg = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not installed",
)


def make_video(path, seconds):
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y",
            "-f", "lavfi", "-i", f"testsrc=duration={seconds}:size=64x64:rate=10",
            "-pix_fmt", "yuv420p",
            str(path),
        ],
        check=True,
    )


@needs_ffmpeg
def test_real_complete_video_passes(tmp_path):
    video = tmp_path / "ok.mp4"
    make_video(video, 3)

    assert download.is_complete_media(
        str(video), 3, subprocess_module=subprocess
    )


@needs_ffmpeg
def test_real_truncated_video_fails(tmp_path):
    video = tmp_path / "cut.mp4"
    make_video(video, 3)

    # cut the file in half, like a disk filling up mid-write
    data = video.read_bytes()
    video.write_bytes(data[: len(data) // 2])

    assert not download.is_complete_media(
        str(video), 3, subprocess_module=subprocess
    )


@needs_ffmpeg
def test_real_short_video_fails_length_check(tmp_path):
    video = tmp_path / "short.mp4"
    make_video(video, 1)

    assert not download.is_complete_media(
        str(video), 30, subprocess_module=subprocess
    )
