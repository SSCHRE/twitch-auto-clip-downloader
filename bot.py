import requests
import subprocess
import time
import json
import os
import db
import datetime
import re
import sys

# ---------------- LOAD CONFIG ----------------
with open("config.json", "r") as f:
    config = json.load(f)

CLIENT_ID = config["client_id"]
CLIENT_SECRET = config["client_secret"]
CHANNELS = config.get("channels", [])
INTERVAL = config.get("check_interval_seconds", 60)
SHORT_ID_LENGTH = config.get("short_id_length", 6)
YT_DLP_QUIET = config.get("yt_dlp_quiet", False)

if not isinstance(CHANNELS, list) or len(CHANNELS) == 0:
    raise ValueError("config.json must contain at least 1 channel in 'channels' array")

db.init_db()

print("Config loaded:", config)
print("Channels:", CHANNELS)

# ---------------- AUTH ----------------
def get_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, params=params)
    r.raise_for_status()
    return r.json()["access_token"]

TOKEN = get_token()

headers = {
    "Client-ID": CLIENT_ID,
    "Authorization": f"Bearer {TOKEN}"
}

# ---------------- CACHE ----------------
game_cache = {}

# ---------------- USER ID ----------------
def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def get_user_id(username):
    url = f"https://api.twitch.tv/helix/users?login={username}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    data = r.json().get("data", [])
    if not data:
        print(f"User not found: {username}")
        return None

    return data[0]["id"]

# ---------------- GAME NAME RESOLVER ----------------
def get_game_name(game_id):
    if not game_id:
        return "Unknown"

    if game_id in game_cache:
        return game_cache[game_id]

    url = f"https://api.twitch.tv/helix/games?id={game_id}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    data = r.json().get("data", [])
    if not data:
        return "Unknown"

    name = data[0]["name"]
    game_cache[game_id] = name
    return name

# ---------------- GET CLIPS ----------------
def get_clips(user_id):
    now = datetime.datetime.utcnow()
    started_at = (now - datetime.timedelta(days=5)).isoformat("T") + "Z"

    url = (
        f"https://api.twitch.tv/helix/clips"
        f"?broadcaster_id={user_id}"
        f"&started_at={started_at}"
        f"&first=100"
    )

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    data = r.json().get("data", [])

    # enforce consistent ordering
    data.sort(key=lambda c: c["created_at"], reverse=True)

    return data

# ---------------- DOWNLOAD ----------------
def download_clip(clip, channel):
    url = clip["url"]

    game_name = safe_name(get_game_name(clip.get("game_id")))
    title = safe_name(clip["title"])
    short_id = clip["id"][:SHORT_ID_LENGTH]

    # convert ISO timestamp → YYYY-MM-DD
    date_folder = clip["created_at"][:10]

    folder = os.path.join("clips", channel, game_name, date_folder)
    os.makedirs(folder, exist_ok=True)

    filename = f"{title}_{short_id}.%(ext)s"

    print(f"[DOWNLOAD] {channel} ({game_name} / {date_folder}) → {title}")

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
print("Bot started...")

user_ids = {}

# Resolve user IDs once
for ch in CHANNELS:
    print("Resolving user:", ch)
    uid = get_user_id(ch)
    if uid:
        user_ids[ch] = uid
        print("Got ID:", uid)

print("\nStarting monitoring loop...\n")

# ---------------- LOOP ----------------
while True:
    for channel, uid in user_ids.items():
        print(f"\n[CHECK] {channel} ({uid})")

        clips = get_clips(uid)

        if not clips:
            print("[WARN] No clips returned")
            continue

        print(f"[INFO] {channel}: fetched {len(clips)} clips")

        for clip in clips:
            clip_id = clip["id"]
            clip_time = clip["created_at"]
            title = clip["title"]

            # PRIMARY DEDUPE
            if db.has_clip(clip_id):
                continue

            print(f"[NEW CLIP] {channel}: {title}")

            try:
                # download first
                success = download_clip(clip, channel)

                if not success:
                    print(f"[SKIP] Download failed: {clip_id}")
                    continue

                # ONLY save after success
                db.save_clip(
                    clip_id,
                    channel,
                    title,
                    clip["url"]
                )

                db.save_latest_clip_time(channel, clip_time)

                print(f"[SAVED] {clip_id}")

            except Exception as e:
                print(f"[ERROR] Failed to process {clip_id}: {e}")

    print(f"\n[SLEEP] Waiting {INTERVAL} seconds...\n")
    time.sleep(INTERVAL)