from io import BytesIO
from urllib import error, parse

import pytest
import sms
from sms import MoceanSMSError


class _DummyResponse:
    def __init__(self, status=200, body='{"ok":true}'):
        self.status = status
        self._body = body.encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_send_sms_uses_bearer_token_auth(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "token-123")
    monkeypatch.setitem(sms.config, "mocean_api_key", "")
    monkeypatch.setitem(sms.config, "mocean_api_secret", "")
    monkeypatch.setitem(sms.config, "mocean_sender", "MatchUp")

    captured = {}

    def fake_urlopen(req, timeout=10):
        captured["headers"] = dict(req.header_items())
        captured["payload"] = parse.parse_qs(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _DummyResponse(status=200, body='{"status":"0"}')

    monkeypatch.setattr(sms.request, "urlopen", fake_urlopen)

    result = sms.send_sms(phone_number="32483126390", message="hello")

    assert result["http_status"] == 200
    assert captured["headers"]["Authorization"] == "Bearer token-123"
    assert captured["payload"]["mocean-to"] == ["32483126390"]
    assert captured["payload"]["mocean-text"] == ["hello"]
    assert "mocean-api-key" not in captured["payload"]
    assert "mocean-api-secret" not in captured["payload"]


def test_send_sms_falls_back_to_key_secret(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "")
    monkeypatch.setitem(sms.config, "mocean_api_key", "legacy-key")
    monkeypatch.setitem(sms.config, "mocean_api_secret", "legacy-secret")
    monkeypatch.setitem(sms.config, "mocean_sender", "MatchUp")

    captured = {}

    def fake_urlopen(req, timeout=10):
        captured["headers"] = dict(req.header_items())
        captured["payload"] = parse.parse_qs(req.data.decode("utf-8"))
        return _DummyResponse(status=200, body='{"status":"0"}')

    monkeypatch.setattr(sms.request, "urlopen", fake_urlopen)

    result = sms.send_sms(phone_number="32483126390", message="hello")

    assert result["http_status"] == 200
    assert "Authorization" not in captured["headers"]
    assert captured["payload"]["mocean-api-key"] == ["legacy-key"]
    assert captured["payload"]["mocean-api-secret"] == ["legacy-secret"]


def test_send_sms_without_credentials_raises(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "")
    monkeypatch.setitem(sms.config, "mocean_api_key", "")
    monkeypatch.setitem(sms.config, "mocean_api_secret", "")

    with pytest.raises(MoceanSMSError) as exc:
        sms.send_sms(phone_number="32483126390", message="hello")

    assert "Mocean credentials are not configured" in str(exc.value)


def test_send_sms_prefers_token_over_key_secret_when_both_set(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "token-abc")
    monkeypatch.setitem(sms.config, "mocean_api_key", "legacy-key")
    monkeypatch.setitem(sms.config, "mocean_api_secret", "legacy-secret")
    monkeypatch.setitem(sms.config, "mocean_sender", "MatchUp")

    captured = {}

    def fake_urlopen(req, timeout=10):
        captured["headers"] = dict(req.header_items())
        captured["payload"] = parse.parse_qs(req.data.decode("utf-8"))
        return _DummyResponse(status=200, body='{"status":"0"}')

    monkeypatch.setattr(sms.request, "urlopen", fake_urlopen)

    sms.send_sms(phone_number="32483126390", message="hello")

    assert captured["headers"]["Authorization"] == "Bearer token-abc"
    assert "mocean-api-key" not in captured["payload"]
    assert "mocean-api-secret" not in captured["payload"]


def test_send_sms_empty_response_body_returns_none(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "token-123")

    def fake_urlopen(req, timeout=10):
        return _DummyResponse(status=202, body="")

    monkeypatch.setattr(sms.request, "urlopen", fake_urlopen)

    result = sms.send_sms(phone_number="32483126390", message="hello")

    assert result["http_status"] == 202
    assert result["response"] is None


def test_send_sms_non_json_response_body_is_preserved(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "token-123")

    def fake_urlopen(req, timeout=10):
        return _DummyResponse(status=200, body="queued")

    monkeypatch.setattr(sms.request, "urlopen", fake_urlopen)

    result = sms.send_sms(phone_number="32483126390", message="hello")

    assert result["http_status"] == 200
    assert result["response"] == "queued"


def test_send_sms_http_error_contains_status_and_body(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "token-123")

    def fake_urlopen(req, timeout=10):
        raise error.HTTPError(
            url=req.full_url,
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=BytesIO(b"invalid token"),
        )

    monkeypatch.setattr(sms.request, "urlopen", fake_urlopen)

    with pytest.raises(MoceanSMSError) as exc:
        sms.send_sms(phone_number="32483126390", message="hello")

    assert "Mocean returned HTTP 401" in str(exc.value)
    assert "invalid token" in str(exc.value)


def test_send_sms_url_error_contains_reason(monkeypatch):
    monkeypatch.setitem(sms.config, "mocean_api_token", "token-123")

    def fake_urlopen(req, timeout=10):
        raise error.URLError("network down")

    monkeypatch.setattr(sms.request, "urlopen", fake_urlopen)

    with pytest.raises(MoceanSMSError) as exc:
        sms.send_sms(phone_number="32483126390", message="hello")

    assert "Mocean request failed" in str(exc.value)
    assert "network down" in str(exc.value)


