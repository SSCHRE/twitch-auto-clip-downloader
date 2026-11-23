import json
import logging
import os
import shutil


def load_config(path="config.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(
            "config.json not found. Copy config.example.json and fill in your credentials."
        )

    with open(path, "r") as f:
        return json.load(f)


def validate_general_config(
    client_id,
    client_secret,
    interval,
    short_id_length,
    channels,
    clip_folder_order,
    clip_name_format,
    clip_lookback_days,
    enable_vod_download,
    vod_lookback_days,
    vod_name_format,
):
    if not isinstance(client_id, str) or client_id.strip() == "":
        raise ValueError("'client_id' must not be empty")

    if not isinstance(client_secret, str) or client_secret.strip() == "":
        raise ValueError("'client_secret' must not be empty")

    if interval < 30:
        raise ValueError("'check_interval_seconds' must be at least 30")

    if short_id_length < 1:
        raise ValueError("'short_id_length' must be at least 1")

    if not isinstance(channels, list) or len(channels) == 0:
        raise ValueError(
            "config.json must contain at least 1 channel in 'channels' array"
        )

    if clip_folder_order not in ("game_date", "date_game"):
        raise ValueError(
            "'clip_folder_order' must be either 'game_date' or 'date_game'"
        )

    if clip_name_format not in ("title", "random", "timestamp"):
        raise ValueError(
            "'clip_name_format' must be 'title', 'random', or 'timestamp'"
        )

    if clip_name_format != "title":
        logging.info(
            "clip_name_format is set to %s; short_id_length is ignored",
            clip_name_format,
        )

    if clip_lookback_days < 1:
        raise ValueError("'clip_lookback_days' must be at least 1")

    if clip_lookback_days > 15:
        logging.warning(
            "clip_lookback_days is set to %d days; Twitch may miss clips "
            "beyond the first 1000 results in a single query",
            clip_lookback_days,
        )

    if not isinstance(enable_vod_download, bool):
        raise ValueError("'enable_vod_download' must be true or false")

    if vod_lookback_days < 1:
        raise ValueError("'vod_lookback_days' must be at least 1")

    if vod_name_format not in ("title", "random", "timestamp"):
        raise ValueError(
            "'vod_name_format' must be 'title', 'random', or 'timestamp'"
        )

    if enable_vod_download:
        logging.info(
            "VOD download enabled: archives from the last %d days will be "
            "downloaded (currently live streams are skipped)",
            vod_lookback_days,
        )

        if vod_name_format != "title":
            logging.info(
                "vod_name_format is set to %s; short_id_length is ignored",
                vod_name_format,
            )


def find_rclone_executable():
    return shutil.which("rclone")


def validate_rclone_config(
    enable_rclone,
    rclone_remotes,
    rclone_command,
    rclone_args,
    rclone_destination,
    rclone_show_progress,
    *,
    delete_local_after_upload=False,
):
    if not isinstance(enable_rclone, bool):
        raise ValueError("'enable_rclone' must be true or false")

    if not isinstance(rclone_remotes, list):
        raise ValueError("'rclone_remotes' must be an array")

    if enable_rclone and len(rclone_remotes) == 0:
        raise ValueError(
            "'rclone_remotes' must contain at least one remote when enable_rclone is true"
        )

    if rclone_command not in ("copy", "sync", "move"):
        raise ValueError("'rclone_command' must be 'copy', 'sync' or 'move'")

    if not isinstance(rclone_args, list):
        raise ValueError("'rclone_args' must be an array")

    if not isinstance(rclone_destination, str):
        raise ValueError("'rclone_destination' must be a string")

    if enable_rclone and not rclone_destination:
        raise ValueError(
            "'rclone_destination' must be specified when enable_rclone is true"
        )

    if enable_rclone and find_rclone_executable() is None:
        raise ValueError(
            "'rclone' command not found on PATH. Install rclone or disable enable_rclone."
        )

    if not isinstance(rclone_show_progress, bool):
        raise ValueError("'rclone_show_progress' must be true or false")

    if not isinstance(delete_local_after_upload, bool):
        raise ValueError("'delete_local_after_upload' must be true or false")

    if delete_local_after_upload and not enable_rclone:
        logging.warning(
            "delete_local_after_upload has no effect while enable_rclone "
            "is false; local files are kept"
        )

    if (
        delete_local_after_upload
        and enable_rclone
        and rclone_command != "copy"
    ):
        raise ValueError(
            "delete_local_after_upload requires rclone_command to be 'copy' "
            "so remote files are not deleted when local files are removed"
        )

    if delete_local_after_upload and enable_rclone:
        logging.info(
            "Local files will be deleted after a successful rclone upload"
        )
