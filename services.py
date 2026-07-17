from dataclasses import dataclass

from twitch_api import TwitchClient


@dataclass
class TwitchService:
    initialize: object
    twitch_get: object
    game_cache: dict


def create_twitch_service(settings):
    client = TwitchClient(settings.client_id, settings.client_secret)
    game_cache = {}

    def initialize():
        client.initialize()

    def twitch_get(url):
        return client.get(url)

    return TwitchService(
        initialize=initialize,
        twitch_get=twitch_get,
        game_cache=game_cache,
    )
