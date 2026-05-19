"""Slack notification handler — post structured alerts to a Slack webhook.

Sends richly formatted Block Kit messages with event details, status
indicators, and direct links to Elastic/Kibana views.
"""

import logging
import time
from typing import Any

import httpx

from app.config import MISSION_ID, SLACK_WEBHOOK_URL

logger = logging.getLogger("nova7.notify.slack")

# Status-to-emoji mapping for visual indicators in Slack
STATUS_INDICATORS = {
    "CRITICAL": ":red_circle:",
    "WARNING": ":large_yellow_circle:",
    "RESOLVED": ":large_green_circle:",
    "INFO": ":blue_circle:",
}

# Status-to-color mapping for Slack attachment sidebar
STATUS_COLORS = {
    "CRITICAL": "#E01E5A",
    "WARNING": "#ECB22E",
    "RESOLVED": "#2EB67D",
    "INFO": "#36C5F0",
}


def _build_alert_blocks(
    channel_id: int,
    channel_name: str,
    status: str,
    details_url: str,
    extra_context: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Build Slack Block Kit blocks for a structured alert message.

    Parameters
    ----------
    channel_id : int
        The fault channel number (1-20).
    channel_name : str
        Human-readable name of the fault channel.
    status : str
        Alert status: CRITICAL, WARNING, RESOLVED, or INFO.
    details_url : str
        URL to the relevant Elastic/Kibana investigation view.
    extra_context : dict, optional
        Additional key-value pairs to display in the context section.

    Returns
    -------
    list[dict]
        Slack Block Kit blocks array.
    """
    indicator = STATUS_INDICATORS.get(status.upper(), ":white_circle:")
    timestamp = int(time.time())

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{MISSION_ID} Fault Alert — Channel {channel_id}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Status:*\n{indicator} {status.upper()}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Channel:*\n#{channel_id} — {channel_name}",
                },
            ],
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Mission:*\n{MISSION_ID}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time:*\n<!date^{timestamp}^{{date_short_pretty}} at {{time_secs}}|{time.strftime('%Y-%m-%d %H:%M:%S UTC')}>",
                },
            ],
        },
    ]

    # Add extra context fields if provided
    if extra_context:
        context_fields = []
        for key, value in extra_context.items():
            context_fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}",
                }
            )
        # Slack allows max 10 fields per section — split if necessary
        for i in range(0, len(context_fields), 10):
            blocks.append(
                {
                    "type": "section",
                    "fields": context_fields[i : i + 10],
                }
            )

    blocks.append({"type": "divider"})

    # Action button linking to the investigation view
    blocks.append(
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Investigate in Elastic",
                        "emoji": True,
                    },
                    "url": details_url,
                    "style": "primary" if status.upper() == "CRITICAL" else "default",
                    "action_id": f"investigate_channel_{channel_id}",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Dashboard",
                        "emoji": True,
                    },
                    "url": (
                        details_url.split("/app/")[0] + "/app/dashboards"
                        if "/app/" in details_url
                        else details_url
                    ),
                    "action_id": f"dashboard_channel_{channel_id}",
                },
            ],
        }
    )

    return blocks


async def send_slack_alert(
    channel_id: int,
    channel_name: str,
    status: str,
    details_url: str,
    webhook_url: str | None = None,
    extra_context: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Post a structured alert to a Slack webhook.

    Parameters
    ----------
    channel_id : int
        The fault channel number (1-20).
    channel_name : str
        Human-readable name of the fault channel.
    status : str
        Alert status: CRITICAL, WARNING, RESOLVED, or INFO.
    details_url : str
        URL to the relevant Elastic/Kibana investigation view.
    webhook_url : str, optional
        Override Slack webhook URL (defaults to SLACK_WEBHOOK_URL from config).
    extra_context : dict, optional
        Additional key-value pairs to display (e.g. affected_services, subsystem).

    Returns
    -------
    dict
        Result indicating success or failure of the webhook post.
    """
    url = webhook_url or SLACK_WEBHOOK_URL

    if not url:
        logger.error("Slack webhook URL not configured. Set SLACK_WEBHOOK_URL.")
        return {"sent": False, "error": "Slack webhook URL not configured"}

    color = STATUS_COLORS.get(status.upper(), "#808080")
    blocks = _build_alert_blocks(
        channel_id, channel_name, status, details_url, extra_context
    )

    # Build the webhook payload with both blocks (rich) and text (fallback)
    fallback_text = (
        f"[{MISSION_ID}] {status.upper()}: Channel {channel_id} — {channel_name}\n"
        f"Details: {details_url}"
    )

    payload: dict[str, Any] = {
        "text": fallback_text,
        "attachments": [
            {
                "color": color,
                "blocks": blocks,
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            logger.info(
                "Slack alert sent: channel=%d, status=%s, name=%s",
                channel_id,
                status,
                channel_name,
            )
            return {
                "sent": True,
                "channel_id": channel_id,
                "status": status,
                "http_status": response.status_code,
            }
    except httpx.HTTPStatusError as exc:
        error_body = exc.response.text[:500]
        logger.error(
            "Slack webhook error (HTTP %d): %s",
            exc.response.status_code,
            error_body,
        )
        return {
            "sent": False,
            "error": f"HTTP {exc.response.status_code}",
            "detail": error_body,
        }
    except httpx.RequestError as exc:
        logger.error("Slack webhook request failed: %s", exc)
        return {"sent": False, "error": str(exc)}


async def send_resolution_alert(
    channel_id: int,
    channel_name: str,
    details_url: str,
    webhook_url: str | None = None,
    resolution_method: str = "automated",
) -> dict[str, Any]:
    """Send a resolution confirmation alert to Slack.

    Parameters
    ----------
    channel_id : int
        The fault channel number (1-20).
    channel_name : str
        Human-readable name of the fault channel.
    details_url : str
        URL to the relevant Elastic/Kibana view.
    webhook_url : str, optional
        Override Slack webhook URL.
    resolution_method : str
        How the fault was resolved (e.g. "automated", "manual", "ai_agent").

    Returns
    -------
    dict
        Result from the webhook post.
    """
    extra_context = {
        "Resolution": resolution_method.replace("_", " ").title(),
        "Action": "Fault channel returned to STANDBY",
    }
    return await send_slack_alert(
        channel_id=channel_id,
        channel_name=channel_name,
        status="RESOLVED",
        details_url=details_url,
        webhook_url=webhook_url,
        extra_context=extra_context,
    )
