import cleanup


def test_deletes_uploaded_files_and_empty_folders(tmp_path):
    clip_folder = tmp_path / "clips" / "channel" / "Minecraft" / "2026-01-01"
    clip_folder.mkdir(parents=True)
    (clip_folder / "clip.mp4").write_text("data")

    vod_folder = tmp_path / "vods" / "channel" / "2026-01-01"
    vod_folder.mkdir(parents=True)
    (vod_folder / "vod.mp4").write_text("data")

    deleted = cleanup.cleanup_uploaded_files(
        [tmp_path / "clips", tmp_path / "vods"]
    )

    assert deleted == 2
    assert not (tmp_path / "clips" / "channel").exists()
    assert not (tmp_path / "vods" / "channel").exists()
    assert (tmp_path / "clips").exists()
    assert (tmp_path / "vods").exists()


def test_keeps_partial_downloads(tmp_path):
    folder = tmp_path / "clips" / "channel" / "2026-01-01"
    folder.mkdir(parents=True)
    (folder / "done.mp4").write_text("data")
    (folder / "busy.mp4.part").write_text("data")
    (folder / "busy.mp4.ytdl").write_text("data")
    (folder / "busy.part-Frag3").write_text("data")
    (folder / "busy.temp.mp4").write_text("data")

    deleted = cleanup.cleanup_uploaded_files([tmp_path / "clips"])

    assert deleted == 1
    assert not (folder / "done.mp4").exists()
    assert sorted(p.name for p in folder.iterdir()) == [
        "busy.mp4.part",
        "busy.mp4.ytdl",
        "busy.part-Frag3",
        "busy.temp.mp4",
    ]


def test_only_touches_given_folders(tmp_path):
    clip_folder = tmp_path / "clips" / "channel"
    clip_folder.mkdir(parents=True)
    (clip_folder / "clip.mp4").write_text("data")

    vod_folder = tmp_path / "vods" / "channel"
    vod_folder.mkdir(parents=True)
    (vod_folder / "vod.mp4").write_text("data")

    cleanup.cleanup_uploaded_files([tmp_path / "clips"])

    assert not (clip_folder / "clip.mp4").exists()
    assert (vod_folder / "vod.mp4").exists()


def test_handles_missing_folder(tmp_path):
    assert cleanup.cleanup_uploaded_files([tmp_path / "clips"]) == 0


def test_title_with_part_in_name_is_not_partial():
    assert cleanup.is_partial_download("my.party_abc123.mp4") is False
    assert cleanup.is_partial_download("x.temp_abc123.mp4") is False
    assert cleanup.is_partial_download("clip.mp4.part") is True
    assert cleanup.is_partial_download("clip.temp.mp4") is True


def test_has_local_files_ignores_partials(tmp_path):
    folder = tmp_path / "clips" / "channel"
    folder.mkdir(parents=True)
    (folder / "busy.mp4.part").write_text("data")

    assert cleanup.has_local_files([tmp_path / "clips"]) is False

    (folder / "done.mp4").write_text("data")

    assert cleanup.has_local_files([tmp_path / "clips"]) is True
