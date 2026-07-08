from unittest.mock import Mock
import bot

def test_get_user_id_found(monkeypatch):

    fake_response = Mock()

    fake_response.json.return_value = {
        "data": [
            {
                "id": "12345"
            }
        ]
    }

    monkeypatch.setattr(
        bot,
        "twitch_get",
        lambda url: fake_response
    )

    result = bot.get_user_id("testuser")

    assert result == "12345"


def test_get_user_id_missing(monkeypatch):

    fake_response = Mock()

    fake_response.json.return_value = {
        "data": []
    }

    monkeypatch.setattr(
        bot,
        "twitch_get",
        lambda url: fake_response
    )

    result = bot.get_user_id("doesnotexist")

    assert result is None