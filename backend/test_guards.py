"""Self-check for the webhook guards: min-chars, silence buffering, secret, threshold."""
import os

import app
import omi

# 1) fragments shorter than MIN_CHARS are ignored (returns before any network call)
assert app._process_transcript("u", "ok", "conversation", None) == 0
assert app._process_transcript("u", "   ", "realtime", None) == 0

# 2) buffered realtime pieces are joined and flushed as ONE transcript
calls = []
app._process_transcript = lambda uid, text, source, speaker: calls.append((uid, text, source)) or 1
app._buffers["sess"] = ["can a first", "year student join"]
app._flush_realtime("sess", "u1")
assert calls == [("u1", "can a first year student join", "realtime")], calls
assert "sess" not in app._buffers and "sess" not in app._timers

# 3) webhook secret is only enforced when configured
app.OMI_SECRET = ""
assert app._omi_ok(None) and app._omi_ok("anything")
app.OMI_SECRET = "s3cret"
assert app._omi_ok("s3cret") and not app._omi_ok("wrong") and not app._omi_ok(None)

print("ok guards: min-chars, buffering, secret")


# 4) Omi notifications: no-op when unconfigured, posts the message when set
os.environ.pop("OMI_APP_ID", None)
os.environ.pop("OMI_APP_SECRET", None)
assert omi.notify_kind() == "off"
assert omi.notify("u", "hello") == {"sent": False, "mode": "off"}

os.environ["OMI_APP_ID"] = "app123"
os.environ["OMI_APP_SECRET"] = "sek"
captured = {}


class _Resp:
    ok = True
    status_code = 200


def fake_post(url, params=None, headers=None, timeout=None):
    captured.update(url=url, params=params, headers=headers)
    return _Resp()


omi.requests.post = fake_post
receipt = omi.notify("uid-42", "Ramesh is overdue")
assert receipt == {"sent": True, "status": 200, "mode": "omi/live"}, receipt
assert captured["url"] == "https://api.omi.me/v2/integrations/app123/notification"
assert captured["params"] == {"uid": "uid-42", "message": "Ramesh is overdue"}
assert captured["headers"]["Authorization"] == "Bearer sek"
os.environ.pop("OMI_APP_ID", None)
os.environ.pop("OMI_APP_SECRET", None)

print("ok omi: no-op off, posts when configured")


# 5) Omi uid linking: webhooks map to the account, notifications target the linked uid
import secrets
import sqlite3

import auth

tag = secrets.token_hex(4)
acct = auth.signup(f"link-{tag}@example.com", "password123")
try:
    assert app._ledger_uid("omiclaim") == "omiclaim"          # unlinked device keeps its raw uid
    auth.set_omi_uid(acct["id"], "omiclaim")
    assert auth.user_by_omi_uid("omiclaim")["uid"] == acct["uid"]
    assert app._ledger_uid("omiclaim") == acct["uid"]          # linked webhook lands in the account
    token = auth.create_session(acct)
    assert app._notify_uid(f"Bearer {token}", "demo") == "omiclaim"   # nudge goes to the linked Omi
    assert app._notify_uid(None, "demo") == "demo"                     # unauthed stays put
    assert auth.public_user(auth.user_for_token(token))["omi_uid"] == "omiclaim"
    auth.set_omi_uid(acct["id"], "")                          # clearing the link reverts mapping
    assert app._ledger_uid("omiclaim") == "omiclaim"
finally:
    with sqlite3.connect(auth.DB) as c:
        c.execute("DELETE FROM sessions WHERE user_id = ?", (acct["id"],))
        c.execute("DELETE FROM users WHERE id = ?", (acct["id"],))

print("ok omi-link: webhook mapping + notify target")


# 6) conversation payload parsing covers the shapes Omi really sends
assert app._conversation_text({"transcript_segments": [{"text": "can first", "speaker": "S0"}, {"text": "years join"}]}) == ("can first years join", "S0")
assert app._conversation_text({"segments": [{"text": "hi"}]}) == ("hi", None)
assert app._conversation_text({"structured": {"overview": "He promised a wardrobe."}}) == ("He promised a wardrobe.", None)
assert app._conversation_text({"transcript": "plain"}) == ("plain", None)
assert app._conversation_text("just a string") == ("just a string", None)
assert app._conversation_text({"nothing": 1}) == ("", None)

print("ok omi-parse: segments / structured.overview / transcript / text")


# 7) real-time webhook resends the cumulative transcript each burst: replace, never append
app.OMI_SECRET = ""
app.on_realtime(app.BackgroundTasks(), uid="u", session_id="s1", payload=[{"text": "Ramesh"}])
app.on_realtime(app.BackgroundTasks(), uid="u", session_id="s1", payload=[{"text": "Ramesh wardrobe"}, {"text": "by Sunday"}])
with app._buf_lock:
    assert app._buffers["s1"] == ["Ramesh wardrobe by Sunday"], app._buffers["s1"]
    if app._timers.get("s1"):
        app._timers["s1"].cancel()
    app._buffers.pop("s1", None)
    app._timers.pop("s1", None)

print("ok omi-realtime: cumulative replace, no duplicate stack")

