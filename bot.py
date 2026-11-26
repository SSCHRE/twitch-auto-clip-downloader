import logging
import shutil
import subprocess
import sys

import db
import twitch_api
import app
import services
from cleanup import (
    cleanup_uploaded_files as _cleanup_uploaded_files,
    has_local_files as _has_local_files,
)
from download import (
    safe_name,
    download_clip as _download_clip,
    download_vod as _download_vod,
    is_complete_media as _is_complete_media,
)
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

VERIFY_DOWNLOADS = shutil.which("ffprobe") is not None
if not VERIFY_DOWNLOADS:
    logging.warning(
        "ffprobe not found on PATH; downloads will not be checked for "
        "corruption. Install ffmpeg to enable this."
    )
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
ENABLE_VOD_DOWNLOAD = _settings.enable_vod_download
VOD_LOOKBACK_DAYS = _settings.vod_lookback_days
VOD_NAME_FORMAT = _settings.vod_name_format
DELETE_LOCAL_AFTER_UPLOAD = _settings.delete_local_after_upload
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


def get_videos(user_id):
    live_stream_id = twitch_api.get_live_stream_id(twitch_get, user_id)
    return twitch_api.get_videos(
        twitch_get,
        user_id,
        VOD_LOOKBACK_DAYS,
        exclude_stream_id=live_stream_id,
    )


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
        ENABLE_VOD_DOWNLOAD,
        VOD_LOOKBACK_DAYS,
        VOD_NAME_FORMAT,
        ENABLE_RCLONE,
        RCLONE_REMOTES,
        RCLONE_COMMAND,
        RCLONE_ARGS,
        RCLONE_DESTINATION,
        RCLONE_SHOW_PROGRESS,
        delete_local_after_upload=DELETE_LOCAL_AFTER_UPLOAD,
    )


def verify_file(path, expected_seconds):
    return _is_complete_media(
        path,
        expected_seconds,
        subprocess_module=subprocess,
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
        verify_file=verify_file if VERIFY_DOWNLOADS else None,
    )


def download_vod(video, channel):
    return _download_vod(
        video,
        channel,
        short_id_length=SHORT_ID_LENGTH,
        vod_name_format=VOD_NAME_FORMAT,
        yt_dlp_quiet=YT_DLP_QUIET,
        show_progress=RCLONE_SHOW_PROGRESS,
        subprocess_module=subprocess,
        verify_file=verify_file if VERIFY_DOWNLOADS else None,
    )


def local_folders():
    folders = ["clips"]
    if ENABLE_VOD_DOWNLOAD:
        folders.append("vods")
    return folders


def run_rclone():
    rclone_command = RCLONE_COMMAND

    if DELETE_LOCAL_AFTER_UPLOAD and ENABLE_RCLONE:
        rclone_command = "copy"

    return _run_rclone(
        enable_rclone=ENABLE_RCLONE,
        rclone_remotes=RCLONE_REMOTES,
        rclone_destination=RCLONE_DESTINATION,
        rclone_command=rclone_command,
        rclone_args=RCLONE_ARGS,
        rclone_show_progress=RCLONE_SHOW_PROGRESS,
        subprocess_module=subprocess,
        local_folders=local_folders(),
    )


def cleanup_uploaded_files():
    return _cleanup_uploaded_files(local_folders())


def has_local_files():
    return _has_local_files(local_folders())


def main():
    app.run(
        channels=CHANNELS,
        interval=INTERVAL,
        enable_rclone=ENABLE_RCLONE,
        enable_vod_download=ENABLE_VOD_DOWNLOAD,
        cleanup_uploaded_files=(
            cleanup_uploaded_files
            if DELETE_LOCAL_AFTER_UPLOAD and ENABLE_RCLONE
            else None
        ),
        has_local_files=has_local_files,
        initialize=initialize,
        get_user_id=get_user_id,
        get_clips=get_clips,
        download_clip=download_clip,
        run_rclone=run_rclone,
        has_clip=db.has_clip,
        save_clip=db.save_clip,
        get_unuploaded_clips=db.get_unuploaded_clips,
        mark_all_uploaded=db.mark_all_uploaded,
        get_videos=get_videos,
        download_vod=download_vod,
        has_vod=db.has_vod,
        save_vod=db.save_vod,
        get_unuploaded_vods=db.get_unuploaded_vods,
        mark_all_vods_uploaded=db.mark_all_vods_uploaded,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stopping bot...")
