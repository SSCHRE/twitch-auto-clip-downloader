import db
import datetime

def test_clip_does_not_exist(tmp_path, monkeypatch):
    database = tmp_path / "test.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(database)
    )

    db.init_db()

    assert db.has_clip("abc123") is False


def test_save_clip(tmp_path, monkeypatch):
    database = tmp_path / "test.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(database)
    )

    db.init_db()

    db.save_clip(
        "abc123",
        "testchannel",
        "test title",
        "https://twitch.tv/test"
    )

    assert db.has_clip("abc123") is True


def test_save_clip_stores_created_at(tmp_path, monkeypatch):
    database = tmp_path / "test.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(database),
    )

    db.init_db()

    db.save_clip(
        "abc123",
        "testchannel",
        "test title",
        "https://twitch.tv/test",
        "2026-01-01T12:00:00Z",
    )

    conn = __import__("sqlite3").connect(database)
    row = conn.execute(
        "SELECT created_at FROM clips WHERE clip_id = ?",
        ("abc123",),
    ).fetchone()
    conn.close()

    assert row[0] == "2026-01-01T12:00:00Z"


def test_delete_clips_before(tmp_path, monkeypatch):
    database = tmp_path / "test.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(database),
    )

    db.init_db()

    db.save_clip(
        "old-clip",
        "channel",
        "old",
        "url",
        "2026-01-01T12:00:00Z",
    )
    db.save_clip(
        "recent-clip",
        "channel",
        "recent",
        "url",
        "2026-01-10T12:00:00Z",
    )

    deleted = db.delete_clips_before(datetime.date(2026, 1, 5))

    assert deleted == 1
    assert db.has_clip("old-clip") is False
    assert db.has_clip("recent-clip") is True


def test_delete_clips_by_id_prefix(tmp_path, monkeypatch):
    database = tmp_path / "test.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(database),
    )

    db.init_db()

    conn = __import__("sqlite3").connect(database)
    conn.execute(
        "INSERT INTO clips (clip_id, channel, title, url, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("AwkwardHelplessSalamander", "channel", "title", "url", None),
    )
    conn.commit()
    conn.close()

    deleted = db.delete_clips_by_id_prefix("Awkward")

    assert deleted == 1
    assert db.has_clip("AwkwardHelplessSalamander") is False


def test_duplicate_clip_is_ignored(tmp_path, monkeypatch):
    database = tmp_path / "test.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(database)
    )

    db.init_db()

    db.save_clip(
        "abc123",
        "channel",
        "title",
        "url"
    )

    db.save_clip(
        "abc123",
        "channel",
        "different title",
        "different url"
    )

    assert db.has_clip("abc123") is True