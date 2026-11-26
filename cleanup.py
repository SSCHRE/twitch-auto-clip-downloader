import logging
import os

# yt-dlp leftovers from interrupted downloads, as rclone filter patterns
PARTIAL_DOWNLOAD_PATTERNS = ("*.part", "*.part-Frag*", "*.ytdl", "*.temp.*")


def is_partial_download(filename):
    # keep these so yt-dlp can resume them
    stem, _ext = os.path.splitext(filename)
    return (
        filename.endswith((".part", ".ytdl"))
        or ".part-Frag" in filename
        or stem.endswith(".temp")
    )


def has_local_files(folders):
    for folder in folders:
        for _root, _dirs, files in os.walk(folder):
            if any(not is_partial_download(f) for f in files):
                return True

    return False


def cleanup_uploaded_files(folders):
    deleted_files = 0
    deleted_folders = 0

    for folder in folders:
        if not os.path.isdir(folder):
            continue

        for root, _dirs, files in os.walk(folder, topdown=False):
            for filename in files:
                if is_partial_download(filename):
                    continue

                os.remove(os.path.join(root, filename))
                deleted_files += 1

            if os.path.normpath(root) == os.path.normpath(folder):
                continue

            try:
                if not os.listdir(root):
                    os.rmdir(root)
                    deleted_folders += 1
            except OSError:
                pass

    if deleted_files:
        logging.info(
            "Deleted %d uploaded local files (%d empty folders removed)",
            deleted_files,
            deleted_folders,
        )

    return deleted_files
