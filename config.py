import json
import logging
import os


def load_config(path="config.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(
            "config.json not found. Copy config.example.json and fill in your credentials."
        )

    with open(path, "r") as f:
        return json.load(f)


def validate_general_config(
    interval,
    short_id_length,
    channels,
    clip_folder_order,
    clip_lookback_days,
):
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

    if clip_lookback_days < 1:
        raise ValueError("'clip_lookback_days' must be at least 1")

    if clip_lookback_days > 15:
        logging.warning(
            "clip_lookback_days is set to %d days",
            clip_lookback_days,
        )


def validate_rclone_config(
    enable_rclone,
    rclone_remotes,
    rclone_command,
    rclone_args,
    rclone_destination,
    rclone_show_progress,
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

    if not isinstance(rclone_show_progress, bool):
        raise ValueError("'rclone_show_progress' must be true or false")
