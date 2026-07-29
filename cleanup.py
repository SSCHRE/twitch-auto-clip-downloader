import datetime
import logging
import os
import re
import shutil

DATE_FOLDER_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_date_folder(name):
    return DATE_FOLDER_PATTERN.match(name) is not None


def parse_date_folder(name):
    if not is_date_folder(name):
        return None

    return datetime.date.fromisoformat(name)


def find_date_folders(clips_root):
    if not os.path.isdir(clips_root):
        return []

    date_folders = []

    for root, dirs, _files in os.walk(clips_root):
        for dir_name in dirs:
            if is_date_folder(dir_name):
                date_folders.append(os.path.join(root, dir_name))

    return date_folders


def prune_empty_parents(path, stop_at):
    stop_at = os.path.normpath(stop_at)
    current = os.path.dirname(path)

    while current and os.path.normpath(current) != stop_at:
        if not os.path.isdir(current):
            break

        try:
            if os.listdir(current):
                break
            os.rmdir(current)
            logging.info("Removed empty folder %s", current)
        except OSError:
            break

        current = os.path.dirname(current)


def clip_id_prefix_from_filename(filename, short_id_length):
    stem, _ext = os.path.splitext(filename)
    if len(stem) <= short_id_length:
        return None

    separator_index = len(stem) - short_id_length - 1
    if stem[separator_index] != "_":
        return None

    return stem[separator_index + 1:]


def cleanup_old_local_clips(
    *,
    clips_root="clips",
    lookback_days,
    today=None,
    short_id_length=None,
    delete_clips_before=None,
    delete_clips_by_id_prefix=None,
):
    if today is None:
        today = datetime.date.today()

    cutoff = today - datetime.timedelta(days=lookback_days)
    deleted_files = 0
    deleted_folders = 0
    deleted_db = 0

    for folder_path in find_date_folders(clips_root):
        folder_date = parse_date_folder(os.path.basename(folder_path))

        if folder_date is None or folder_date >= cutoff:
            continue

        if delete_clips_by_id_prefix and short_id_length:
            for _root, _dirs, files in os.walk(folder_path):
                for filename in files:
                    prefix = clip_id_prefix_from_filename(
                        filename,
                        short_id_length,
                    )
                    if prefix:
                        deleted_db += delete_clips_by_id_prefix(prefix)

        file_count = sum(
            len(files)
            for _root, _dirs, files in os.walk(folder_path)
        )

        shutil.rmtree(folder_path)
        deleted_files += file_count
        deleted_folders += 1
        prune_empty_parents(folder_path, clips_root)

        logging.info(
            "Deleted local clip folder %s (%d files)",
            folder_path,
            file_count,
        )

    if delete_clips_before:
        deleted_db += delete_clips_before(cutoff)

    if deleted_folders:
        logging.info(
            "Local cleanup removed %d folders and %d files outside "
            "the %d day lookback window",
            deleted_folders,
            deleted_files,
            lookback_days,
        )

    if deleted_db:
        logging.info(
            "Removed %d clip records from database outside "
            "the %d day lookback window",
            deleted_db,
            lookback_days,
        )

    return deleted_files
