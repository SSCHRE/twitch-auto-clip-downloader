import os
import re
import sys
import logging


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


def download_clip(
    clip,
    channel,
    *,
    short_id_length,
    clip_folder_order,
    yt_dlp_quiet,
    show_progress,
    get_game_name,
    subprocess_module,
):
    url = clip["url"]

    game_name = safe_name(get_game_name(clip.get("game_id")))
    title = safe_name(clip["title"])
    short_id = clip["id"][:short_id_length]
    date_folder = clip["created_at"][:10]

    if clip_folder_order == "game_date":
        folder = os.path.join("clips", channel, game_name, date_folder)
    else:
        folder = os.path.join("clips", channel, date_folder, game_name)

    os.makedirs(folder, exist_ok=True)

    filename = f"{title}_{short_id}.%(ext)s"

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
    return result.returncode == 0
