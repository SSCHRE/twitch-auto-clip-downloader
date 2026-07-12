import db

def test_new_clip_is_not_uploaded(tmp_path, monkeypatch):
    db_file = tmp_path / "clips.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(db_file)
    )

    db.init_db()

    db.save_clip(
        "abc123",
        "channel",
        "title",
        "url"
    )

    assert db.is_uploaded("abc123") is False


def test_mark_uploaded(tmp_path, monkeypatch):
    db_file = tmp_path / "clips.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(db_file)
    )

    db.init_db()

    db.save_clip(
        "abc123",
        "channel",
        "title",
        "url"
    )

    db.mark_uploaded("abc123")

    assert db.is_uploaded("abc123") is True


def test_get_unuploaded_clips(tmp_path, monkeypatch):
    db_file = tmp_path / "clips.db"

    monkeypatch.setattr(
        db,
        "DB_FILE",
        str(db_file)
    )

    db.init_db()

    db.save_clip(
        "abc123",
        "channel",
        "title",
        "url"
    )

    db.save_clip(
        "xyz789",
        "channel",
        "title2",
        "url2"
    )

    db.mark_uploaded("xyz789")

    result = db.get_unuploaded_clips()

    assert result == ["abc123"]