import db

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