import logging
from dataclasses import dataclass

from config import load_config, validate_general_config, validate_rclone_config


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    channels: list
    interval: int
    short_id_length: int
    yt_dlp_quiet: bool
    clip_folder_order: str
    clip_lookback_days: int
    enable_rclone: bool
    rclone_remotes: list
    rclone_destination: str
    rclone_command: str
    rclone_args: list
    rclone_show_progress: bool

    @classmethod
    def load(cls, path="config.json"):
        config = load_config(path)
        return cls(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            channels=config.get("channels", []),
            interval=config.get("check_interval_seconds", 60),
            short_id_length=config.get("short_id_length", 6),
            yt_dlp_quiet=config.get("yt_dlp_quiet", False),
            clip_folder_order=config.get("clip_folder_order", "game_date"),
            clip_lookback_days=config.get("clip_lookback_days", 1),
            enable_rclone=config.get("enable_rclone", False),
            rclone_remotes=config.get("rclone_remotes", []),
            rclone_destination=config.get("rclone_destination", "TwitchClips"),
            rclone_command=config.get("rclone_command", "copy"),
            rclone_args=config.get("rclone_args", []),
            rclone_show_progress=config.get("rclone_show_progress", False),
        )

    def validate(self):
        validate_general_config(
            self.client_id,
            self.client_secret,
            self.interval,
            self.short_id_length,
            self.channels,
            self.clip_folder_order,
            self.clip_lookback_days,
        )
        validate_rclone_config(
            self.enable_rclone,
            self.rclone_remotes,
            self.rclone_command,
            self.rclone_args,
            self.rclone_destination,
            self.rclone_show_progress,
        )


def validate_runtime(
    client_id,
    client_secret,
    interval,
    short_id_length,
    channels,
    clip_folder_order,
    clip_lookback_days,
    enable_rclone,
    rclone_remotes,
    rclone_command,
    rclone_args,
    rclone_destination,
    rclone_show_progress,
):
    validate_general_config(
        client_id,
        client_secret,
        interval,
        short_id_length,
        channels,
        clip_folder_order,
        clip_lookback_days,
    )
    validate_rclone_config(
        enable_rclone,
        rclone_remotes,
        rclone_command,
        rclone_args,
        rclone_destination,
        rclone_show_progress,
    )


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
