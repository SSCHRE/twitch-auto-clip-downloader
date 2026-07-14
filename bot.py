import requests
import subprocess
import time
import json
import os
import db
import datetime
import re
import sys
import logging

# ---------------- LOAD CONFIG ----------------
if not os.path.exists("config.json"):
    raise FileNotFoundError(
        "config.json not found. Copy config.example.json and fill in your credentials."
    )
    
with open("config.json", "r") as f:
    config = json.load(f)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
CHANNELS = config.get("channels", [])
INTERVAL = config.get("check_interval_seconds", 60)
SHORT_ID_LENGTH = config.get("short_id_length", 6)
YT_DLP_QUIET = config.get("yt_dlp_quiet", False)
CLIP_FOLDER_ORDER = config.get("clip_folder_order", "game_date")
CLIP_LOOKBACK_DAYS = config.get("clip_lookback_days", 1)

# rclone
ENABLE_RCLONE = config.get("enable_rclone", False)
RCLONE_REMOTES = config.get("rclone_remotes", [])
RCLONE_DESTINATION = config.get("rclone_destination", "TwitchClips")
RCLONE_COMMAND = config.get("rclone_command", "copy")
RCLONE_ARGS = config.get("rclone_args", [])
RCLONE_SHOW_PROGRESS = config.get("rclone_show_progress", False)

def validate_config():
    validate_general_config()
    validate_rclone_config()

def validate_general_config():
    if INTERVAL < 30:
        raise ValueError("'check_interval_seconds' must be at least 30")

    if SHORT_ID_LENGTH < 1:
        raise ValueError("'short_id_length' must be at least 1")

    if not isinstance(CHANNELS, list) or len(CHANNELS) == 0:
        raise ValueError(
            "config.json must contain at least 1 channel in 'channels' array"
        )

    if CLIP_FOLDER_ORDER not in ("game_date", "date_game"):
        raise ValueError(
            "'clip_folder_order' must be either 'game_date' or 'date_game'"
        )

    if CLIP_LOOKBACK_DAYS < 1:
        raise ValueError(
            "'clip_lookback_days' must be at least 1"
        )

    if CLIP_LOOKBACK_DAYS > 15:
        logging.warning(
            "clip_lookback_days is set to %d days",
            CLIP_LOOKBACK_DAYS
        )

def validate_rclone_config():
    if not isinstance(ENABLE_RCLONE, bool):
        raise ValueError("'enable_rclone' must be true or false")

    if not isinstance(RCLONE_REMOTES, list):
        raise ValueError(
            "'rclone_remotes' must be an array"
        )

    if ENABLE_RCLONE and len(RCLONE_REMOTES) == 0:
        raise ValueError(
            "'rclone_remotes' must contain at least one remote when enable_rclone is true"
        )

    if RCLONE_COMMAND not in ("copy", "sync", "move"):
        raise ValueError(
            "'rclone_command' must be 'copy', 'sync' or 'move'"
        )

    if not isinstance(RCLONE_ARGS, list):
        raise ValueError(
            "'rclone_args' must be an array"
        )

    if not isinstance(RCLONE_DESTINATION, str):
        raise ValueError("'rclone_destination' must be a string")

    if ENABLE_RCLONE and not RCLONE_DESTINATION:
        raise ValueError(
            "'rclone_destination' must be specified when enable_rclone is true"
        )

    if not isinstance(RCLONE_SHOW_PROGRESS, bool):
        raise ValueError(
            "'rclone_show_progress' must be true or false"
        )

validate_config()
db.init_db()

logging.info("Config loaded")
logging.info("Channels: %s", CHANNELS)

# ---------------- AUTH ----------------
TOKEN = None
headers = {}

def initialize():
    refresh_token()

def get_token():
    logging.info("Requesting Twitch API access token")

    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    try:
        r = requests.post(
            url,
            params=params,
            timeout=10
        )

        r.raise_for_status()

        token = r.json()["access_token"]

        logging.info("Successfully obtained Twitch API access token")

        return token

    except requests.RequestException as e:
        logging.error("Failed to obtain Twitch API token: %s", e)
        raise


def refresh_token():
    global TOKEN, headers

    TOKEN = get_token()

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {TOKEN}"
    }


def twitch_get(url):
    global headers

    r = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    if r.status_code == 401:
        logging.warning("Twitch token expired, refreshing token")

        refresh_token()

        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )

    r.raise_for_status()

    return r

# ---------------- CACHE ----------------
game_cache = {}

# ---------------- USER ID ----------------
def safe_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)

    name = name.strip()
    name = name.rstrip(".")

    if not name:
        name = "Unknown"

    # Windows reserved names
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4",
        "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4",
        "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }

    if name.upper() in reserved:
        name = f"_{name}"

    return name

def get_user_id(username):
    url = f"https://api.twitch.tv/helix/users?login={username}"

    r = twitch_get(url)

    data = r.json().get("data", [])

    if not data:
        logging.warning("User not found: %s", username)
        return None

    return data[0]["id"]

# ---------------- GAME NAME RESOLVER ----------------
def get_game_name(game_id):
    if not game_id:
        return "Unknown"

    if game_id in game_cache:
        return game_cache[game_id]

    url = f"https://api.twitch.tv/helix/games?id={game_id}"
    r = twitch_get(url)
    r.raise_for_status()

    data = r.json().get("data", [])
    if not data:
        return "Unknown"

    name = data[0]["name"]
    game_cache[game_id] = name
    return name

# ---------------- GET CLIPS ----------------
def get_clips(user_id):
    now = datetime.datetime.now(datetime.UTC)
    started_at = (
        now - datetime.timedelta(days=5)
    ).isoformat().replace("+00:00", "Z")

    url = (
        f"https://api.twitch.tv/helix/clips"
        f"?broadcaster_id={user_id}"
        f"&started_at={started_at}"
        f"&first=100"
    )

    r = twitch_get(url)
    r.raise_for_status()

    data = r.json().get("data", [])

    data.sort(key=lambda c: c["created_at"], reverse=True)

    return data

# ---------------- DOWNLOAD ----------------
def download_clip(clip, channel):
    url = clip["url"]

    game_name = safe_name(get_game_name(clip.get("game_id")))
    title = safe_name(clip["title"])
    short_id = clip["id"][:SHORT_ID_LENGTH]

    date_folder = clip["created_at"][:10]

    if CLIP_FOLDER_ORDER == "game_date":
        folder = os.path.join(
            "clips",
            channel,
            game_name,
            date_folder
        )

    else:
        folder = os.path.join(
            "clips",
            channel,
            date_folder,
            game_name
        )

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
        url
    ]

    if YT_DLP_QUIET:
        cmd.append("--quiet")

    if RCLONE_SHOW_PROGRESS:
        stdout = None
        stderr = None
    else:
        stdout = subprocess.DEVNULL
        stderr = subprocess.DEVNULL


    result = subprocess.run(
        cmd,
        stdout=stdout,
        stderr=stderr,
    )

    return result.returncode == 0

# ---------------- RCLONE ----------------
def run_rclone():
    if not ENABLE_RCLONE:
        return True

    overall_success = True

    logging.info(
        "Starting rclone %s → %s",
        RCLONE_COMMAND,
        RCLONE_REMOTES
    )

    for remote in RCLONE_REMOTES:

        destination = f"{remote}:{RCLONE_DESTINATION}"

        cmd = [
            "rclone",
            RCLONE_COMMAND,
            "clips",
            destination
        ]

        if RCLONE_SHOW_PROGRESS:
            cmd.append("--progress")

        cmd.extend(RCLONE_ARGS)

        logging.info(
            "RCLONE - Uploading clips → %s",
            destination
        )

        try:
            if RCLONE_SHOW_PROGRESS:
                stdout = None
                stderr = None
            else:
                stdout = subprocess.DEVNULL
                stderr = subprocess.DEVNULL


            result = subprocess.run(
                cmd,
                stdout=stdout,
                stderr=stderr,
            )

            if result.returncode == 0:
                logging.info(
                    "rclone completed successfully → %s",
                    destination
                )

            else:
                logging.error(
                    "rclone failed for %s with exit code: %d",
                    destination,
                    result.returncode
                )
                overall_success = False

        except FileNotFoundError:
            logging.error(
                "rclone was not found. Install rclone or disable enable_rclone."
            )
            return False

        except Exception:
            logging.exception(
                "Unexpected error while running rclone for %s",
                destination
            )
            overall_success = False

    return overall_success

# ---------------- MAIN ----------------
def main():
    logging.info("Bot started...")
    
    initialize()
    user_ids = {}

    for ch in CHANNELS:
        logging.info("Resolving user: %s", ch)
        uid = get_user_id(ch)
        if uid:
            user_ids[ch] = uid
            logging.info("Resolved user ID: %s", uid)

    while True:
        downloaded_any = False

        for channel, uid in user_ids.items():
            logging.info("Checking channel: %s (%s)", channel, uid)

            clips = get_clips(uid)

            if not clips:
                logging.info("[WARN] No clips returned")
                continue

            logging.info("Fetched %d clips for %s", len(clips), channel)

            for clip in clips:
                clip_id = clip["id"]
                clip_time = clip["created_at"]
                title = clip["title"]

                if db.has_clip(clip_id):
                    continue

                logging.info("New clip found for %s: %s", channel, title)

                try:
                    success = download_clip(clip, channel)

                    if not success:
                        logging.warning("Skipping clip because download failed: %s", clip_id)
                        continue

                    db.save_clip(
                        clip_id,
                        channel,
                        title,
                        clip["url"]
                    )

                    downloaded_any = True

                    logging.info("Saved clip: %s", clip_id)

                except KeyboardInterrupt:
                    raise

                except Exception as e:
                    logging.exception("Failed to process clip %s", clip_id)

        if ENABLE_RCLONE:

            pending_uploads = db.get_unuploaded_clips()

            if pending_uploads:
                logging.info(
                    "%d clips waiting for upload",
                    len(pending_uploads)
                )

                if run_rclone():
                    db.mark_all_uploaded()

                    logging.info(
                        "Marked %d clips as uploaded",
                        len(pending_uploads)
                    )

        logging.info("Waiting %d seconds before next check", INTERVAL)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Stopping bot...")
