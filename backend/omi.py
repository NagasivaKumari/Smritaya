"""Omi outbound — closing the loop.

Inbound speech arrives via the webhooks in app.py. This module is the other
direction: the witness pushes a drafted reminder back to the user's own phone
through Omi's notifications API.

  POST https://api.omi.me/v2/integrations/{app_id}/notification?uid=&message=
  Auth: Bearer <OMI_APP_SECRET>

Needs OMI_APP_ID + OMI_APP_SECRET (Omi developer portal). Unconfigured = a
no-op that reports "off", so the reminder still drafts and logs without Omi.
"""

from __future__ import annotations

import os

import requests

NOTIFY_URL = "https://api.omi.me/v2/integrations/{app_id}/notification"


def configured() -> bool:
    return bool(os.environ.get("OMI_APP_ID") and os.environ.get("OMI_APP_SECRET"))


def notify_kind() -> str:
    return "omi/live" if configured() else "off"


def notify(uid: str, message: str, timeout: int = 15) -> dict:
    """Push a notification to the user's Omi. Never raises — reports instead."""
    app_id = os.environ.get("OMI_APP_ID", "").strip()
    secret = os.environ.get("OMI_APP_SECRET", "").strip()
    if not (app_id and secret):
        return {"sent": False, "mode": "off"}
    try:
        r = requests.post(
            NOTIFY_URL.format(app_id=app_id),
            params={"uid": uid, "message": message},
            headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
            timeout=timeout,
        )
        return {"sent": r.ok, "status": r.status_code, "mode": "omi/live"}
    except Exception as e:  # network down / bad host — the reminder still stands
        return {"sent": False, "mode": "omi/error", "error": str(e)}
