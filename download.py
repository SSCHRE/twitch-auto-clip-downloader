import glob
import os
import re
import sys
import logging
import uuid

from cleanup import is_partial_download

# A download shorter than this share of the length Twitch reports is
# treated as truncated (e.g. the disk filled up while writing it)
MIN_DURATION_RATIO = 0.9


def safe_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip()
    name = name.rstrip(".")

    if not name:
        name = "Unknown"

    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4",
        "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4",
        "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    }

    if name.upper() in reserved:
        name = f"_{name}"

    return name


TIMESTAMP_ID_LENGTH = 8


def parse_twitch_duration(value):
    """Clips report seconds as a number, VODs a string like '1h2m3s'."""
    if isinstance(value, (int, float)):
        return float(value)

    if not value:
        return None

    match = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", value)
    if not match or not any(match.groups()):
        return None

    hours, minutes, seconds = (int(g or 0) for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def probe_duration(path, *, subprocess_module):
    result = subprocess_module.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def is_complete_media(path, expected_seconds, *, subprocess_module):
    duration = probe_duration(path, subprocess_module=subprocess_module)

    if duration is None or duration <= 0:
        logging.error("Downloaded file is unreadable: %s", path)
        return False

    if expected_seconds and duration < expected_seconds * MIN_DURATION_RATIO:
        logging.error(
            "Downloaded file is truncated: %s (%.0fs of %.0fs)",
            path,
            duration,
            expected_seconds,
        )
        return False

    return True


def find_downloaded_files(folder, filename):
    base = filename[: -len(".%(ext)s")]
    pattern = os.path.join(glob.escape(folder), glob.escape(base) + ".*")

    return [
        path
        for path in glob.glob(pattern)
        if not is_partial_download(os.path.basename(path))
    ]


def verify_download(folder, filename, expected_seconds, verify_file):
    files = find_downloaded_files(folder, filename)

    if not files:
        logging.error(
            "yt-dlp reported success but no file was found for %s",
            os.path.join(folder, filename),
        )
        return False

    broken = [
        path
        for path in files
        if not verify_file(path, expected_seconds)
    ]

    # remove broken files so the next check downloads them again
    for path in broken:
        os.remove(path)
        logging.warning("Deleted broken download %s", path)

    return not broken


def clip_id_suffix(clip_id: str) -> str:
    unique_part = clip_id.rsplit("-", 1)[-1]
    return unique_part[:TIMESTAMP_ID_LENGTH]


def format_clip_timestamp(created_at: str) -> str:
    return created_at[:10] + "_" + created_at[11:19].replace(":", "-")


def build_clip_filename(
    clip,
    *,
    clip_name_format,
    short_id_length,
    unique_suffix=None,
):
    if clip_name_format == "title":
        short_id = clip["id"][:short_id_length]
        base = f"{safe_name(clip['title'])}_{short_id}"
    elif clip_name_format == "random":
        token = unique_suffix or uuid.uuid4().hex[:12]
        base = f"clip_{token}"
    elif clip_name_format == "timestamp":
        base = f"{format_clip_timestamp(clip['created_at'])}_{clip_id_suffix(clip['id'])}"
    else:
        raise ValueError(
            f"Unsupported clip_name_format: {clip_name_format}"
        )

    return f"{base}.%(ext)s"


def download_clip(
    clip,
    channel,
    *,
    short_id_length,
    clip_folder_order,
    clip_name_format,
    yt_dlp_quiet,
    show_progress,
    get_game_name,
    subprocess_module,
    verify_file=None,
):
    url = clip["url"]

    game_name = safe_name(get_game_name(clip.get("game_id")))
    title = safe_name(clip["title"])
    date_folder = clip["created_at"][:10]

    if clip_folder_order == "game_date":
        folder = os.path.join("clips", channel, game_name, date_folder)
    else:
        folder = os.path.join("clips", channel, date_folder, game_name)

    os.makedirs(folder, exist_ok=True)

    filename = build_clip_filename(
        clip,
        clip_name_format=clip_name_format,
        short_id_length=short_id_length,
    )

    logging.info(
        "Downloading clip: %s (%s / %s) → %s",
        channel,
        game_name,
        date_folder,
        title,
    )

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-overwrites",
        "-o", os.path.join(folder, filename),
        url,
    ]

    if yt_dlp_quiet:
        cmd.append("--quiet")

    if show_progress:
        stdout = None
        stderr = None
    else:
        stdout = subprocess_module.DEVNULL
        stderr = subprocess_module.DEVNULL

    result = subprocess_module.run(cmd, stdout=stdout, stderr=stderr)
    if result.returncode != 0:
        return False

    if verify_file is None:
        return True

    return verify_download(
        folder,
        filename,
        parse_twitch_duration(clip.get("duration")),
        verify_file,
    )


def build_vod_filename(
    video,
    *,
    vod_name_format,
    short_id_length,
    unique_suffix=None,
):
    if vod_name_format == "title":
        short_id = video["id"][:short_id_length]
        base = f"{safe_name(video['title'])}_{short_id}"
    elif vod_name_format == "random":
        token = unique_suffix or uuid.uuid4().hex[:12]
        base = f"vod_{token}"
    elif vod_name_format == "timestamp":
        created_at = video.get("published_at") or video["created_at"]
        base = f"{format_clip_timestamp(created_at)}_{video['id'][:TIMESTAMP_ID_LENGTH]}"
    else:
        raise ValueError(
            f"Unsupported vod_name_format: {vod_name_format}"
        )

    return f"{base}.%(ext)s"


def download_vod(
    video,
    channel,
    *,
    short_id_length,
    vod_name_format,
    yt_dlp_quiet,
    show_progress,
    subprocess_module,
    verify_file=None,
):
    url = video["url"]
    title = safe_name(video["title"])
    date_folder = (video.get("published_at") or video["created_at"])[:10]
    folder = os.path.join("vods", channel, date_folder)

    os.makedirs(folder, exist_ok=True)

    filename = build_vod_filename(
        video,
        vod_name_format=vod_name_format,
        short_id_length=short_id_length,
    )

    logging.info(
        "Downloading VOD: %s (%s) → %s",
        channel,
        date_folder,
        title,
    )

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-overwrites",
        "-o", os.path.join(folder, filename),
        url,
    ]

    if yt_dlp_quiet:
        cmd.append("--quiet")

    if show_progress:
        stdout = None
        stderr = None
    else:
        stdout = subprocess_module.DEVNULL
        stderr = subprocess_module.DEVNULL

    result = subprocess_module.run(cmd, stdout=stdout, stderr=stderr)
    if result.returncode != 0:
        return False

    if verify_file is None:
        return True

    return verify_download(
        folder,
        filename,
        parse_twitch_duration(video.get("duration")),
        verify_file,
    )
