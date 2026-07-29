# Twitch automatic clip downloader

Automatically downloads newly created Twitch clips from one or more channels.

## Features

- Monitors one or multiple Twitch channels for newly created clips  
- Customizable check interval (polling-based)  
- Supports duplicate clip names (e.g. bot-generated clips or repeated titles)
- Configurable clip filename format: title, random, or timestamp (all include a unique clip ID suffix)
- Keeps track of already downloaded clips through a SQLite database
- Automatically saves clips into a local `/clips` folder  
  - Organized by channel/game/date for easier navigation
- Supports rclone to automatically upload new clips after downloading.
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
