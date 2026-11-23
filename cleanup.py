import logging
import os


def is_partial_download(filename):
    # yt-dlp leftovers from interrupted downloads; keep them so it can resume
    return (
        ".part" in filename
        or filename.endswith(".ytdl")
        or ".temp." in filename
    )


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
