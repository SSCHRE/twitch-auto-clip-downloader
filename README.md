# Twitch automatic clip downloader

Automatically downloads newly created Twitch clips (and optionally full VODs) from one or more channels.

## Features

- Monitors one or multiple Twitch channels for newly created clips  
- Optional full VOD (past broadcast archive) downloads
  - Skips the stream that is currently live; only completed archives are downloaded
- Customizable check interval (polling-based)  
- Supports duplicate clip names (e.g. bot-generated clips or repeated titles)
- Keeps track of already downloaded clips and VODs through a SQLite database
- Automatically saves clips into a local `/clips` folder  
  - Organized by channel/game/date for easier navigation
- Saves VODs into a local `/vods` folder organized by channel/date
- Supports rclone to automatically upload new clips (and VODs) after downloading.
  - Requires environment variable `rclone` command to be available
- Configurable clip folder structure
  - Supports `game_date` layout:
    ```
    clips/
    └── ChannelName/
        └── GameName/
            └── YYYY-MM-DD/
                └── clip.mp4
    ```
  - Supports `date_game` layout:
    ```
    clips/
    └── ChannelName/
        └── YYYY-MM-DD/
            └── GameName/
                └── clip.mp4
    ```
  - VOD layout:
    ```
    vods/
    └── ChannelName/
        └── YYYY-MM-DD/
            └── vod.mp4
    ```

## Info

This is an early version of the project and may receive updates and improvements over time.

The current implementation uses periodic checks to detect new clips via the Twitch API.

## Requirements

- Python 3.8+
- Required libraries:
  - requests
  - yt-dlp
  - pytest
- Twitch API credentials (Client ID + Client Secret)
- Rclone added on system variables, IF rclone is used

## Setup

1. Clone the repository (or download the files)

2. Install dependencies:

`pip install -r requirements.txt`

3. Configure the bot:

Make a copy of `config.example.json` and name it `config.json` and add your Twitch API credentials and settings.

4. Run the bot:

`python bot.py`

## Clip naming

Set `clip_name_format` in `config.json`:

| Value | Example filename |
|-------|------------------|
| `title` | `Cool Clip_abcdef.%(ext)s` |
| `random` | `clip_a1b2c3d4e5f6.%(ext)s` |
| `timestamp` | `2026-01-01_12-00-00_TKUHVRWr.%(ext)s` |

`short_id_length` only applies to the `title` format. Random names use a generated token; timestamp names append a short clip ID suffix from the Twitch API (the unique part after `-` in the clip ID, up to 8 characters).

## VOD downloads

Set `enable_vod_download` to `true` to also download completed past-broadcast archives.

- Uses Twitch Helix `/videos` with `type=archive`
- Checks `vod_lookback_days` (default `7`)
- Skips any VOD whose `stream_id` matches the channel's currently live stream, so in-progress broadcasts are never downloaded
- After a stream ends, the finished archive is picked up on a later poll
- Naming uses `vod_name_format` (`title` / `random` / `timestamp`), same options as clips
- Files are stored under `vods/{channel}/{YYYY-MM-DD}/`
- When rclone is enabled, VODs upload to `{rclone_destination}/vods`

## Delete local files after upload

Set `delete_local_after_upload` to `true` to remove local clips and VODs once rclone has uploaded them.

- Only runs when `enable_rclone` is `true`
- Files are deleted only after rclone succeeded for **every** remote; if any upload fails, local files are kept and retried on the next check
- Only deletes files under the local `clips/` (and `vods/`, when VOD download is enabled) folders, and removes the empty folders left behind
- Unfinished yt-dlp downloads (`.part`, `.ytdl`) are kept so they can resume
- Records stay in `clips.db`, so deleted clips and VODs are not downloaded again
- Does not delete anything from your rclone remotes

`rclone_command` must be `copy`. The bot will refuse to start with `sync` or `move`, because `sync` would delete remote files once the local copies are gone.

`delete_local_clips_outside_lookback` and `delete_local_vods_outside_lookback` have been replaced by this option; the bot logs a warning if they are still in `config.json`.

## Disclaimer

This project is intended for personal, educational, and lawful use only.

By using this software, you agree to comply with all applicable terms and policies of the Twitch platform and any APIs used.

You are strictly prohibited from:
- Using this tool to spam, overload, or abuse Twitch services or APIs
- Attempting to bypass or violate API rate limits
- Downloading, redistributing, or using content without proper rights or permission
- Using this tool in any way that could harm, disrupt, or interfere with platform services or users

API usage may be subject to rate limits, restrictions, or blocking at any time by Twitch.

The author is not responsible for any misuse of this software or any consequences resulting from its use.

This project is provided "as-is", without warranties or guarantees of any kind.
