from __future__ import annotations

import json
from urllib import error, parse, request

from config import config_data as config


class MoceanSMSError(RuntimeError):
    """Raised when the Mocean SMS provider rejects or cannot process a request."""


def send_sms(phone_number: str, message: str, sender: str | None = None, timeout: int = 10) -> dict:
    """Send a single SMS through Mocean.

    The helper is intentionally small so it can be mocked in tests and reused by
    future reminder jobs once match scheduling exists.
    """
    phone_number = (phone_number or "").strip()
    message = (message or "").strip()

    if not phone_number:
        raise MoceanSMSError("phone_number is required")
    if not message:
        raise MoceanSMSError("message is required")

    api_token = (config.get("mocean_api_token") or "").strip()
    api_key = (config.get("mocean_api_key") or "").strip()
    api_secret = (config.get("mocean_api_secret") or "").strip()

    sms_url = config.get("mocean_sms_url", "https://rest.moceanapi.com/rest/2/sms")
    payload_dict = {
        "mocean-from": sender or config.get("mocean_sender", "MatchUp"),
        "mocean-to": phone_number,
        "mocean-text": message,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    elif api_key and api_secret:
        # Backward-compatible mode for older Mocean credentials.
        payload_dict["mocean-api-key"] = api_key
        payload_dict["mocean-api-secret"] = api_secret
    else:
        raise MoceanSMSError(
            "Mocean credentials are not configured (set MOCEAN_API_TOKEN or MOCEAN_API_KEY/MOCEAN_API_SECRET)"
        )

    payload = parse.urlencode(payload_dict).encode("utf-8")

    req = request.Request(
        sms_url,
        data=payload,
        method="POST",
        headers=headers,
    )

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw_body = resp.read().decode("utf-8", errors="replace")
            if not raw_body:
                return {"http_status": resp.status, "response": None}

            try:
                parsed_body = json.loads(raw_body)
            except json.JSONDecodeError:
                parsed_body = raw_body

            return {"http_status": resp.status, "response": parsed_body}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        detail = body or exc.reason or "unknown error"
        raise MoceanSMSError(f"Mocean returned HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise MoceanSMSError(f"Mocean request failed: {exc.reason}") from exc

