from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import twitch_api


def _mock_response(data, cursor=None):
    payload = {"data": data}
    if cursor is not None:
        payload["pagination"] = {"cursor": cursor}
    response = Mock()
    response.json.return_value = payload
    return response


def test_get_live_stream_id_returns_id_when_live():
    get_fn = Mock(return_value=_mock_response([{"id": "stream-99"}]))

    assert twitch_api.get_live_stream_id(get_fn, "12345") == "stream-99"
    assert "streams?user_id=12345" in get_fn.call_args[0][0]


def test_get_live_stream_id_returns_none_when_offline():
    get_fn = Mock(return_value=_mock_response([]))

    assert twitch_api.get_live_stream_id(get_fn, "12345") is None


def test_get_videos_uses_archive_type_and_period():
    now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    get_fn = Mock(return_value=_mock_response([]))

    with patch("twitch_api.datetime.datetime", wraps=datetime) as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.UTC = UTC
        mock_datetime.timedelta = timedelta
        mock_datetime.fromisoformat = datetime.fromisoformat
        twitch_api.get_videos(get_fn, "12345", lookback_days=7)

    url = get_fn.call_args[0][0]
    assert "type=archive" in url
    assert "period=week" in url
    assert "user_id=12345" in url


def test_get_videos_excludes_live_stream_vod():
    now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    get_fn = Mock(
        return_value=_mock_response(
            [
                {
                    "id": "live-vod",
                    "stream_id": "stream-1",
                    "title": "Live Now",
                    "published_at": "2026-01-15T10:00:00Z",
                    "created_at": "2026-01-15T10:00:00Z",
                    "url": "https://www.twitch.tv/videos/live-vod",
                },
                {
                    "id": "done-vod",
                    "stream_id": "stream-0",
                    "title": "Yesterday",
                    "published_at": "2026-01-14T10:00:00Z",
                    "created_at": "2026-01-14T10:00:00Z",
                    "url": "https://www.twitch.tv/videos/done-vod",
                },
            ]
        )
    )

    with patch("twitch_api.datetime.datetime", wraps=datetime) as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.UTC = UTC
        mock_datetime.timedelta = timedelta
        mock_datetime.fromisoformat = datetime.fromisoformat
        videos = twitch_api.get_videos(
            get_fn,
            "12345",
            lookback_days=7,
            exclude_stream_id="stream-1",
        )

    assert [video["id"] for video in videos] == ["done-vod"]


def test_get_videos_filters_by_lookback_days():
    now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    get_fn = Mock(
        return_value=_mock_response(
            [
                {
                    "id": "recent",
                    "stream_id": "s1",
                    "published_at": "2026-01-14T10:00:00Z",
                    "created_at": "2026-01-14T10:00:00Z",
                },
                {
                    "id": "old",
                    "stream_id": "s0",
                    "published_at": "2026-01-01T10:00:00Z",
                    "created_at": "2026-01-01T10:00:00Z",
                },
            ]
        )
    )

    with patch("twitch_api.datetime.datetime", wraps=datetime) as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.UTC = UTC
        mock_datetime.timedelta = timedelta
        mock_datetime.fromisoformat = datetime.fromisoformat
        videos = twitch_api.get_videos(get_fn, "12345", lookback_days=3)

    assert [video["id"] for video in videos] == ["recent"]
