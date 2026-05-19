"""Twilio notification handler — SMS + Voice calls via Twilio REST API.

Uses httpx directly (no Twilio SDK required). Sends SMS alerts with event
summaries and deep links, and initiates voice calls using TwiML.
"""

import logging
from typing import Any

import httpx

from app.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
    TWILIO_TO_NUMBER,
)

logger = logging.getLogger("nova7.notify.twilio")

# Twilio REST API base URL
TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


def _get_auth() -> tuple[str, str]:
    """Return HTTP Basic Auth credentials for the Twilio API."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError(
            "Twilio credentials not configured. "
            "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables."
        )
    return (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def _get_messages_url() -> str:
    """Return the Twilio Messages resource URL."""
    return f"{TWILIO_API_BASE}/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"


def _get_calls_url() -> str:
    """Return the Twilio Calls resource URL."""
    return f"{TWILIO_API_BASE}/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"


async def send_sms(
    event_summary: str,
    deep_link: str,
    to_number: str | None = None,
    from_number: str | None = None,
) -> dict[str, Any]:
    """Send an SMS alert via Twilio with the event summary and a deep link.

    Parameters
    ----------
    event_summary : str
        A human-readable summary of the event (e.g. "Channel 4 — GPS Multipath
        Interference detected on navigation, sensor-validator").
    deep_link : str
        A URL linking directly to the relevant Elastic/Kibana view.
    to_number : str, optional
        Override recipient phone number (defaults to TWILIO_TO_NUMBER).
    from_number : str, optional
        Override sender phone number (defaults to TWILIO_FROM_NUMBER).

    Returns
    -------
    dict
        Twilio API response containing message SID and status, or error details.
    """
    to = to_number or TWILIO_TO_NUMBER
    sender = from_number or TWILIO_FROM_NUMBER

    if not to or not sender:
        logger.error("Twilio phone numbers not configured (FROM=%s, TO=%s)", sender, to)
        return {"error": "Phone numbers not configured", "sent": False}

    body = f"[NOVA-7 ALERT]\n" f"{event_summary}\n" f"\n" f"Investigate: {deep_link}"

    payload = {
        "To": to,
        "From": sender,
        "Body": body,
    }

    try:
        auth = _get_auth()
    except ValueError as exc:
        logger.error("Twilio auth error: %s", exc)
        return {"error": str(exc), "sent": False}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                _get_messages_url(),
                data=payload,
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()
            logger.info(
                "SMS sent successfully: SID=%s, to=%s, status=%s",
                result.get("sid"),
                to,
                result.get("status"),
            )
            return {
                "sent": True,
                "sid": result.get("sid"),
                "status": result.get("status"),
                "to": to,
            }
    except httpx.HTTPStatusError as exc:
        error_body = exc.response.text[:500]
        logger.error(
            "Twilio SMS API error (HTTP %d): %s",
            exc.response.status_code,
            error_body,
        )
        return {
            "sent": False,
            "error": f"HTTP {exc.response.status_code}",
            "detail": error_body,
        }
    except httpx.RequestError as exc:
        logger.error("Twilio SMS request failed: %s", exc)
        return {"sent": False, "error": str(exc)}


async def make_voice_call(
    event_summary: str,
    twiml_url: str,
    to_number: str | None = None,
    from_number: str | None = None,
) -> dict[str, Any]:
    """Initiate a voice call via Twilio that plays a TwiML script.

    Parameters
    ----------
    event_summary : str
        A human-readable summary used for logging (the actual spoken content
        is defined in the TwiML at twiml_url).
    twiml_url : str
        A publicly accessible URL serving TwiML XML that Twilio will fetch
        and execute when the call connects. For anomaly detection, use the
        anomaly_detected.xml template; for resolution, use anomaly_resolved.xml.
    to_number : str, optional
        Override recipient phone number (defaults to TWILIO_TO_NUMBER).
    from_number : str, optional
        Override sender phone number (defaults to TWILIO_FROM_NUMBER).

    Returns
    -------
    dict
        Twilio API response containing call SID and status, or error details.
    """
    to = to_number or TWILIO_TO_NUMBER
    sender = from_number or TWILIO_FROM_NUMBER

    if not to or not sender:
        logger.error("Twilio phone numbers not configured (FROM=%s, TO=%s)", sender, to)
        return {"error": "Phone numbers not configured", "called": False}

    payload = {
        "To": to,
        "From": sender,
        "Url": twiml_url,
        "Method": "GET",
    }

    try:
        auth = _get_auth()
    except ValueError as exc:
        logger.error("Twilio auth error: %s", exc)
        return {"error": str(exc), "called": False}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                _get_calls_url(),
                data=payload,
                auth=auth,
            )
            response.raise_for_status()
            result = response.json()
            logger.info(
                "Voice call initiated: SID=%s, to=%s, status=%s, summary=%s",
                result.get("sid"),
                to,
                result.get("status"),
                event_summary[:80],
            )
            return {
                "called": True,
                "sid": result.get("sid"),
                "status": result.get("status"),
                "to": to,
            }
    except httpx.HTTPStatusError as exc:
        error_body = exc.response.text[:500]
        logger.error(
            "Twilio Call API error (HTTP %d): %s",
            exc.response.status_code,
            error_body,
        )
        return {
            "called": False,
            "error": f"HTTP {exc.response.status_code}",
            "detail": error_body,
        }
    except httpx.RequestError as exc:
        logger.error("Twilio voice call request failed: %s", exc)
        return {"called": False, "error": str(exc)}


async def send_alert(
    channel: int,
    channel_name: str,
    event_summary: str,
    deep_link: str,
    twiml_url: str | None = None,
    sms: bool = True,
    voice: bool = False,
) -> dict[str, Any]:
    """Convenience function to send both SMS and/or voice alert for a channel.

    Parameters
    ----------
    channel : int
        The fault channel number (1-20).
    channel_name : str
        Human-readable name of the fault channel.
    event_summary : str
        Description of the event.
    deep_link : str
        URL to the relevant Elastic/Kibana view.
    twiml_url : str, optional
        TwiML URL for voice calls (required if voice=True).
    sms : bool
        Whether to send an SMS (default True).
    voice : bool
        Whether to initiate a voice call (default False).

    Returns
    -------
    dict
        Combined results from SMS and/or voice call attempts.
    """
    results: dict[str, Any] = {"channel": channel, "channel_name": channel_name}

    if sms:
        results["sms"] = await send_sms(event_summary, deep_link)

    if voice and twiml_url:
        results["voice"] = await make_voice_call(event_summary, twiml_url)
    elif voice and not twiml_url:
        logger.warning(
            "Voice call requested but no twiml_url provided for channel %d", channel
        )
        results["voice"] = {"called": False, "error": "No twiml_url provided"}

    return results
