import db


def test_vod_does_not_exist(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_FILE", str(database))
    db.init_db()

    assert db.has_vod("vod123") is False


def test_save_vod(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_FILE", str(database))
    db.init_db()

    db.save_vod(
        "vod123",
        "testchannel",
        "test title",
        "https://www.twitch.tv/videos/vod123",
        "2026-01-01T12:00:00Z",
    )

    assert db.has_vod("vod123") is True


def test_unuploaded_vods_and_mark_all(tmp_path, monkeypatch):
    database = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_FILE", str(database))
    db.init_db()

    db.save_vod(
        "vod123",
        "testchannel",
        "test title",
        "https://www.twitch.tv/videos/vod123",
    )

    assert db.get_unuploaded_vods() == ["vod123"]

    db.mark_all_vods_uploaded()

    assert db.get_unuploaded_vods() == []
