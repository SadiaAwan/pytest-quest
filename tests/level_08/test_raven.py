"""Level 08: test raven delivery without real network calls."""

import json
from unittest.mock import MagicMock
from urllib.error import URLError

import pytest

from dungeon import raven


@pytest.fixture
def mocked_urlopen(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(raven, "urlopen", mock)
    return mock


def fake_response(delivery_id):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(
        {"delivery_id": delivery_id}
    ).encode("utf-8")
    return response


def test_goblin_raven_returns_delivery_id(mocked_urlopen):
    mocked_urlopen.return_value = fake_response("goblin-123")

    result = raven.send_raven("Goblin", "The treasure is safe")

    assert result == "goblin-123"
    mocked_urlopen.assert_called_once()


def test_raven_sends_correct_request(mocked_urlopen):
    mocked_urlopen.return_value = fake_response("delivery-456")

    raven.send_raven("Sadia", "Hello from Stockholm")

    mocked_urlopen.assert_called_once()
    args, kwargs = mocked_urlopen.call_args
    request = args[0]

    assert request.full_url == raven.RAVEN_API
    assert request.get_method() == "POST"
    assert json.loads(request.data.decode("utf-8")) == {
        "to": "Sadia",
        "message": "Hello from Stockholm",
    }
    assert kwargs["timeout"] == raven.TIMEOUT_SECONDS


def test_raven_retries_then_succeeds(mocked_urlopen):
    mocked_urlopen.side_effect = [
        URLError("First attempt failed"),
        URLError("Second attempt failed"),
        fake_response("retry-789"),
    ]

    result = raven.send_raven("Sadia", "Try again", attempts=3)

    assert result == "retry-789"
    assert mocked_urlopen.call_count == 3

    for call in mocked_urlopen.call_args_list:
        assert call.kwargs["timeout"] == raven.TIMEOUT_SECONDS


@pytest.mark.parametrize("attempts", [1, 2, 4])
def test_raven_raises_when_all_attempts_fail(mocked_urlopen, attempts):
    mocked_urlopen.side_effect = URLError("Network unavailable")

    with pytest.raises(raven.RavenLostError):
        raven.send_raven("Sadia", "Important message", attempts=attempts)

    assert mocked_urlopen.call_count == attempts

    for call in mocked_urlopen.call_args_list:
        assert call.kwargs["timeout"] == raven.TIMEOUT_SECONDS