import logging
import subprocess

import db
import twitch_api
import app
import services
from download import safe_name, download_clip as _download_clip
from rclone import run_rclone as _run_rclone
from settings import Settings, setup_logging, validate_runtime

_settings = Settings.load()
setup_logging()
_settings.validate()
db.init_db()

logging.info("Config loaded")
logging.info("Channels: %s", _settings.channels)

# Re-exported for tests and external callers
CLIENT_ID = _settings.client_id
CLIENT_SECRET = _settings.client_secret
CHANNELS = _settings.channels
INTERVAL = _settings.interval
SHORT_ID_LENGTH = _settings.short_id_length
YT_DLP_QUIET = _settings.yt_dlp_quiet
CLIP_FOLDER_ORDER = _settings.clip_folder_order
CLIP_LOOKBACK_DAYS = _settings.clip_lookback_days
ENABLE_RCLONE = _settings.enable_rclone
RCLONE_REMOTES = _settings.rclone_remotes
RCLONE_DESTINATION = _settings.rclone_destination
RCLONE_COMMAND = _settings.rclone_command
RCLONE_ARGS = _settings.rclone_args
RCLONE_SHOW_PROGRESS = _settings.rclone_show_progress

_twitch = services.create_twitch_service(_settings)
game_cache = _twitch.game_cache
initialize = _twitch.initialize


def twitch_get(url):
    return _twitch.twitch_get(url)


def get_user_id(username):
    return twitch_api.get_user_id(twitch_get, username)


def get_game_name(game_id):
    return twitch_api.get_game_name(twitch_get, game_id, game_cache)


def get_clips(user_id):
    return twitch_api.get_clips(twitch_get, user_id, CLIP_LOOKBACK_DAYS)


def validate_config():
    validate_runtime(
        INTERVAL,
        SHORT_ID_LENGTH,
        CHANNELS,
        CLIP_FOLDER_ORDER,
        CLIP_LOOKBACK_DAYS,
        ENABLE_RCLONE,
        RCLONE_REMOTES,
        RCLONE_COMMAND,
        RCLONE_ARGS,
        RCLONE_DESTINATION,
        RCLONE_SHOW_PROGRESS,
    )


def download_clip(clip, channel):
    return _download_clip(
        clip,
        channel,
        short_id_length=SHORT_ID_LENGTH,
        clip_folder_order=CLIP_FOLDER_ORDER,
        yt_dlp_quiet=YT_DLP_QUIET,
        show_progress=RCLONE_SHOW_PROGRESS,
        get_game_name=get_game_name,
        subprocess_module=subprocess,
    )


def run_rclone():
    return _run_rclone(
        enable_rclone=ENABLE_RCLONE,
        rclone_remotes=RCLONE_REMOTES,
        rclone_destination=RCLONE_DESTINATION,
        rclone_command=RCLONE_COMMAND,
        rclone_args=RCLONE_ARGS,
        rclone_show_progress=RCLONE_SHOW_PROGRESS,
        subprocess_module=subprocess,
    )


def main():
    app.run(
        channels=CHANNELS,
        interval=INTERVAL,
        enable_rclone=ENABLE_RCLONE,
        initialize=initialize,
        get_user_id=get_user_id,
        get_clips=get_clips,
        download_clip=download_clip,
        run_rclone=run_rclone,
        has_clip=db.has_clip,
        save_clip=db.save_clip,
        get_unuploaded_clips=db.get_unuploaded_clips,
        mark_all_uploaded=db.mark_all_uploaded,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stopping bot...")
