import datetime
import logging

import requests


class TwitchClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.headers = {}

    def initialize(self):
        self.refresh_token()

    def get_token(self):
        logging.info("Requesting Twitch API access token")

        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        try:
            r = requests.post(url, params=params, timeout=10)
            r.raise_for_status()

            token = r.json()["access_token"]
            logging.info("Successfully obtained Twitch API access token")
            return token

        except requests.RequestException as e:
            logging.error("Failed to obtain Twitch API token: %s", e)
            raise

    def refresh_token(self):
        self.token = self.get_token()
        self.headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self.token}",
        }

    def get(self, url):
        r = requests.get(url, headers=self.headers, timeout=10)

        if r.status_code == 401:
            logging.warning("Twitch token expired, refreshing token")
            self.refresh_token()
            r = requests.get(url, headers=self.headers, timeout=10)

        r.raise_for_status()
        return r


def get_user_id(get_fn, username):
    url = f"https://api.twitch.tv/helix/users?login={username}"
    r = get_fn(url)
    data = r.json().get("data", [])

    if not data:
        logging.warning("User not found: %s", username)
        return None

    return data[0]["id"]


def get_game_name(get_fn, game_id, cache):
    if not game_id:
        return "Unknown"

    if game_id in cache:
        return cache[game_id]

    url = f"https://api.twitch.tv/helix/games?id={game_id}"
    r = get_fn(url)
    r.raise_for_status()

    data = r.json().get("data", [])
    if not data:
        return "Unknown"

    name = data[0]["name"]
    cache[game_id] = name
    return name


def _format_rfc3339_utc(dt):
    return dt.isoformat().replace("+00:00", "Z")


def get_clips(get_fn, user_id, lookback_days):
    now = datetime.datetime.now(datetime.UTC)
    started_at = _format_rfc3339_utc(now - datetime.timedelta(days=lookback_days))
    ended_at = _format_rfc3339_utc(now)

    clips = []
    cursor = None

    while True:
        url = (
            f"https://api.twitch.tv/helix/clips"
            f"?broadcaster_id={user_id}"
            f"&started_at={started_at}"
            f"&ended_at={ended_at}"
            f"&first=100"
        )
        if cursor:
            url += f"&after={cursor}"

        r = get_fn(url)
        r.raise_for_status()

        payload = r.json()
        batch = payload.get("data", [])
        clips.extend(batch)

        cursor = payload.get("pagination", {}).get("cursor")
        if not cursor:
            break

    clips.sort(key=lambda c: c["created_at"], reverse=True)
    return clips


def get_live_stream_id(get_fn, user_id):
    url = f"https://api.twitch.tv/helix/streams?user_id={user_id}"
    r = get_fn(url)
    r.raise_for_status()

    data = r.json().get("data", [])
    if not data:
        return None

    return data[0]["id"]


def _videos_period_for_lookback(lookback_days):
    if lookback_days <= 1:
        return "day"
    if lookback_days <= 7:
        return "week"
    if lookback_days <= 30:
        return "month"
    return "all"


def get_videos(get_fn, user_id, lookback_days, exclude_stream_id=None):
    """Return completed archive VODs within the lookback window.

    Excludes any VOD tied to exclude_stream_id (the currently live broadcast)
    so in-progress streams are never downloaded.
    """
    now = datetime.datetime.now(datetime.UTC)
    cutoff = now - datetime.timedelta(days=lookback_days)
    period = _videos_period_for_lookback(lookback_days)

    videos = []
    cursor = None

    while True:
        url = (
            f"https://api.twitch.tv/helix/videos"
            f"?user_id={user_id}"
            f"&type=archive"
            f"&period={period}"
            f"&sort=time"
            f"&first=100"
        )
        if cursor:
            url += f"&after={cursor}"

        r = get_fn(url)
        r.raise_for_status()

        payload = r.json()
        batch = payload.get("data", [])
        videos.extend(batch)

        cursor = payload.get("pagination", {}).get("cursor")
        if not cursor:
            break

    filtered = []
    for video in videos:
        if exclude_stream_id and video.get("stream_id") == exclude_stream_id:
            logging.info(
                "Skipping in-progress VOD %s (live stream %s)",
                video.get("id"),
                exclude_stream_id,
            )
            continue

        published_at = video.get("published_at") or video.get("created_at")
        if not published_at:
            continue

        published = datetime.datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        )
        if published < cutoff:
            continue

        filtered.append(video)

    filtered.sort(
        key=lambda v: v.get("published_at") or v.get("created_at"),
        reverse=True,
    )
    return filtered
