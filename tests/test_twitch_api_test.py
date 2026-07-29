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


def test_get_clips_includes_started_at_and_ended_at():
    now = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    get_fn = Mock(return_value=_mock_response([]))

    with patch("twitch_api.datetime.datetime", wraps=datetime) as mock_datetime:
        mock_datetime.now.return_value = now
        mock_datetime.UTC = UTC
        mock_datetime.timedelta = timedelta
        twitch_api.get_clips(get_fn, "12345", lookback_days=20)

    url = get_fn.call_args[0][0]
    assert "started_at=2025-12-26T12:00:00Z" in url
    assert "ended_at=2026-01-15T12:00:00Z" in url
    assert "after=" not in url


def test_get_clips_paginates_until_no_cursor():
    page_one = [{"id": "clip-1", "created_at": "2026-01-15T10:00:00Z"}]
    page_two = [{"id": "clip-2", "created_at": "2026-01-14T10:00:00Z"}]
    get_fn = Mock(
        side_effect=[
            _mock_response(page_one, cursor="cursor-1"),
            _mock_response(page_two),
        ]
    )

    clips = twitch_api.get_clips(get_fn, "12345", lookback_days=7)

    assert len(clips) == 2
    assert get_fn.call_count == 2
    assert "after=cursor-1" in get_fn.call_args_list[1][0][0]
    assert clips[0]["id"] == "clip-1"


def test_get_clips_sorts_newest_first():
    get_fn = Mock(
        return_value=_mock_response(
            [
                {"id": "old", "created_at": "2026-01-10T10:00:00Z"},
                {"id": "new", "created_at": "2026-01-15T10:00:00Z"},
            ]
        )
    )

    clips = twitch_api.get_clips(get_fn, "12345", lookback_days=7)

    assert [clip["id"] for clip in clips] == ["new", "old"]
