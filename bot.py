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
TOKEN = None

if INTERVAL < 30:
    raise ValueError("'check_interval_seconds' must be at least 30")

if SHORT_ID_LENGTH < 1:
    raise ValueError("'short_id_length' must be at least 1")

if not isinstance(CHANNELS, list) or len(CHANNELS) == 0:
    raise ValueError("config.json must contain at least 1 channel in 'channels' array")

db.init_db()

logging.info("Config loaded")
logging.info("Channels: %s", CHANNELS)

# ---------------- AUTH ----------------
TOKEN = None
headers = {}


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

refresh_token()

# ---------------- CACHE ----------------
game_cache = {}

# ---------------- USER ID ----------------
def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

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
    started_at = (now - datetime.timedelta(days=5)).isoformat().replace("+00:00", "Z")

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

    folder = os.path.join("clips", channel, game_name, date_folder)
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

    result = subprocess.run(cmd)

    return result.returncode == 0

# ---------------- MAIN ----------------
logging.info("Bot started...")

user_ids = {}

for ch in CHANNELS:
    logging.info("Resolving user: %s", ch)
    uid = get_user_id(ch)
    if uid:
        user_ids[ch] = uid
        logging.info("Resolved user ID: %s", uid)

# ---------------- LOOP ----------------
try:
    while True:
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

                    logging.info("Saved clip: %s", clip_id)

                except Exception:
                    logging.exception("Failed to process clip %s", clip_id)

        logging.info("Waiting %d seconds before next check", INTERVAL)
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    logging.info("\nStopping bot...")