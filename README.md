# Twitch automatic clip downloader

Automatically downloads newly created Twitch clips from one or more channels.

## Features

- Monitors one or multiple Twitch channels for newly created clips  
- Customizable check interval (polling-based)  
- Supports duplicate clip names (e.g. bot-generated clips or repeated titles)  
- Automatically saves clips into a local `/clips` folder  
  - Organized by channel / game / date for easier navigation  

## Info

This is an early version of the project and may receive updates and improvements over time.

The current implementation uses periodic checks to detect new clips via the Twitch API.

## Requirements

- Python 3.8+
- `requests` library
- Twitch API credentials (Client ID + Client Secret)

## Setup

1. Create a `config.json` file:

```json
{
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}
