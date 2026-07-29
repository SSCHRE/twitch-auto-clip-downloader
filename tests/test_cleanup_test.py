import datetime
from pathlib import Path

import cleanup
import db


def test_is_date_folder():
    assert cleanup.is_date_folder("2026-01-01") is True
    assert cleanup.is_date_folder("not-a-date") is False


def test_cleanup_deletes_old_date_folder(tmp_path):
    old_folder = tmp_path / "clips" / "channel" / "Minecraft" / "2026-01-01"
    old_folder.mkdir(parents=True)
    (old_folder / "clip.mp4").write_text("data")

    recent_folder = tmp_path / "clips" / "channel" / "Minecraft" / "2026-01-10"
    recent_folder.mkdir(parents=True)
    (recent_folder / "clip.mp4").write_text("data")

    deleted = cleanup.cleanup_old_local_clips(
        clips_root=tmp_path / "clips",
        lookback_days=1,
        today=datetime.date(2026, 1, 11),
    )

    assert deleted == 1
    assert not old_folder.exists()
    assert recent_folder.exists()


def test_cleanup_keeps_folders_within_lookback(tmp_path):
    folder = tmp_path / "clips" / "channel" / "2026-01-10"
    folder.mkdir(parents=True)
    (folder / "clip.mp4").write_text("data")

    deleted = cleanup.cleanup_old_local_clips(
        clips_root=tmp_path / "clips",
        lookback_days=7,
        today=datetime.date(2026, 1, 11),
    )

    assert deleted == 0
    assert folder.exists()


def test_cleanup_works_for_date_game_layout(tmp_path):
    old_folder = tmp_path / "clips" / "channel" / "2026-01-01" / "Minecraft"
    old_folder.mkdir(parents=True)
    (old_folder / "clip.mp4").write_text("data")

    deleted = cleanup.cleanup_old_local_clips(
        clips_root=tmp_path / "clips",
        lookback_days=1,
        today=datetime.date(2026, 1, 11),
    )

    assert deleted == 1
    assert not (tmp_path / "clips" / "channel" / "2026-01-01").exists()


def test_cleanup_removes_empty_game_folder(tmp_path):
    old_folder = tmp_path / "clips" / "channel" / "R.E.P.O" / "2026-01-01"
    old_folder.mkdir(parents=True)
    (old_folder / "clip.mp4").write_text("data")

    recent_folder = tmp_path / "clips" / "channel" / "Minecraft" / "2026-01-10"
    recent_folder.mkdir(parents=True)
    (recent_folder / "clip.mp4").write_text("data")

    deleted = cleanup.cleanup_old_local_clips(
        clips_root=tmp_path / "clips",
        lookback_days=1,
        today=datetime.date(2026, 1, 11),
    )

    assert deleted == 1
    assert not (tmp_path / "clips" / "channel" / "R.E.P.O").exists()
    assert (tmp_path / "clips" / "channel" / "Minecraft").exists()


def test_cleanup_keeps_game_folder_with_remaining_dates(tmp_path):
    old_folder = tmp_path / "clips" / "channel" / "Minecraft" / "2026-01-01"
    old_folder.mkdir(parents=True)
    (old_folder / "old.mp4").write_text("data")

    recent_folder = tmp_path / "clips" / "channel" / "Minecraft" / "2026-01-10"
    recent_folder.mkdir(parents=True)
    (recent_folder / "recent.mp4").write_text("data")

    deleted = cleanup.cleanup_old_local_clips(
        clips_root=tmp_path / "clips",
        lookback_days=1,
        today=datetime.date(2026, 1, 11),
    )

    assert deleted == 1
    assert (tmp_path / "clips" / "channel" / "Minecraft").exists()
    assert not old_folder.exists()
    assert recent_folder.exists()


def test_cleanup_returns_zero_when_clips_root_missing(tmp_path):
    deleted = cleanup.cleanup_old_local_clips(
        clips_root=tmp_path / "missing",
        lookback_days=1,
        today=datetime.date(2026, 1, 11),
    )

    assert deleted == 0


def test_clip_id_prefix_from_filename():
    assert cleanup.clip_id_prefix_from_filename("My Clip_Awkwar.mp4", 6) == "Awkwar"
    assert cleanup.clip_id_prefix_from_filename("short.mp4", 6) is None


def test_cleanup_deletes_matching_db_records(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_FILE", str(database))
    db.init_db()

    db.save_clip(
        "AwkwardHelplessSalamander",
        "channel",
        "babymetal",
        "url",
        "2026-01-01T12:00:00Z",
    )
    db.save_clip(
        "RecentClipIdentifier",
        "channel",
        "recent",
        "url",
        "2026-01-10T12:00:00Z",
    )

    old_folder = tmp_path / "clips" / "channel" / "R.E.P.O" / "2026-01-01"
    old_folder.mkdir(parents=True)
    (old_folder / "babymetal_Awkwar.mp4").write_text("data")

    cleanup.cleanup_old_local_clips(
        clips_root=tmp_path / "clips",
        lookback_days=1,
        today=datetime.date(2026, 1, 11),
        short_id_length=6,
        delete_clips_before=db.delete_clips_before,
        delete_clips_by_id_prefix=db.delete_clips_by_id_prefix,
    )

    assert db.has_clip("AwkwardHelplessSalamander") is False
    assert db.has_clip("RecentClipIdentifier") is True


def test_find_date_folders_finds_nested_paths(tmp_path):
    folder = tmp_path / "clips" / "channel" / "game" / "2026-01-05"
    folder.mkdir(parents=True)

    found = cleanup.find_date_folders(tmp_path / "clips")

    assert len(found) == 1
    assert Path(found[0]) == folder
