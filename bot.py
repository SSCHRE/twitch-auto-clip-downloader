import logging
import subprocess
import sys

import db
import twitch_api
import app
import services
from cleanup import cleanup_old_local_clips as _cleanup_old_local_clips
from download import safe_name, download_clip as _download_clip
from rclone import run_rclone as _run_rclone
from settings import Settings, setup_logging, validate_runtime

setup_logging()

try:
    _settings = Settings.load()
except FileNotFoundError as exc:
    logging.error("%s", exc)
    if __name__ == "__main__":
        sys.exit(1)
    raise

try:
    _settings.validate()
except ValueError as exc:
    if __name__ == "__main__":
        logging.error("%s", exc)
        sys.exit(1)
    raise
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
CLIP_NAME_FORMAT = _settings.clip_name_format
CLIP_LOOKBACK_DAYS = _settings.clip_lookback_days
DELETE_LOCAL_CLIPS_OUTSIDE_LOOKBACK = (
    _settings.delete_local_clips_outside_lookback
)
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
        CLIENT_ID,
        CLIENT_SECRET,
        INTERVAL,
        SHORT_ID_LENGTH,
        CHANNELS,
        CLIP_FOLDER_ORDER,
        CLIP_NAME_FORMAT,
        CLIP_LOOKBACK_DAYS,
        DELETE_LOCAL_CLIPS_OUTSIDE_LOOKBACK,
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
        clip_name_format=CLIP_NAME_FORMAT,
        yt_dlp_quiet=YT_DLP_QUIET,
        show_progress=RCLONE_SHOW_PROGRESS,
        get_game_name=get_game_name,
        subprocess_module=subprocess,
    )


def run_rclone():
    rclone_command = RCLONE_COMMAND

    if DELETE_LOCAL_CLIPS_OUTSIDE_LOOKBACK and ENABLE_RCLONE:
        rclone_command = "copy"

    return _run_rclone(
        enable_rclone=ENABLE_RCLONE,
        rclone_remotes=RCLONE_REMOTES,
        rclone_destination=RCLONE_DESTINATION,
        rclone_command=rclone_command,
        rclone_args=RCLONE_ARGS,
        rclone_show_progress=RCLONE_SHOW_PROGRESS,
        subprocess_module=subprocess,
    )


def cleanup_local_clips():
    return _cleanup_old_local_clips(
        lookback_days=CLIP_LOOKBACK_DAYS,
        short_id_length=SHORT_ID_LENGTH,
        delete_clips_before=db.delete_clips_before,
        delete_clips_by_id_prefix=db.delete_clips_by_id_prefix,
    )


def main():
    app.run(
        channels=CHANNELS,
        interval=INTERVAL,
        enable_rclone=ENABLE_RCLONE,
        cleanup_local_clips=(
            cleanup_local_clips
            if DELETE_LOCAL_CLIPS_OUTSIDE_LOOKBACK
            else None
        ),
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
