"""Smritaya — the witness for the verbal economy.

Omi (ambient voice) -> this backend -> Qdrant (memory) -> Lyzr (agents) -> answers back.

Endpoints
  POST /omi/conversation   Omi memory-creation webhook (uid query param)
  POST /omi/realtime       Omi real-time transcript webhook (light + fast 200)
  GET  /health             registry status: qdrant / embedder / lyzr modes
  GET  /deeds              filterable ledger (status, counterparty, overdue)
  POST /deeds              manual entry (also used by seed/demo)
  POST /remind             draft + log a reminder for a deed
  POST /status             mark a deed kept / broken
  POST /ask                free-text questioning of the witness (semantic + filtered recall)
  POST /hearing            convene a hearing: 4-act memo for a broken deed
  GET  /chamber/{name}     counterparty dossier + wax seal
  POST /forget             strike points from the record (privacy right)
"""

from __future__ import annotations

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")  # repo-root .env; no --env-file needed

from fastapi import BackgroundTasks, Body, FastAPI, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import agents
import auth
import content
import memory
import omi

DEMO_UID = os.environ.get("SMRITAYA_DEMO_UID", "founder")

# --- Omi webhook guards (workshop-notebook hardening; all optional, sane defaults) ---
OMI_SECRET = os.environ.get("SMRITAYA_OMI_SECRET", "").strip()  # unset = open, as before
MIN_CHARS = int(os.environ.get("SMRITAYA_MIN_CHARS", "8"))       # ignore "uh"/"okay" fragments
SILENCE_SECONDS = float(os.environ.get("SMRITAYA_SILENCE_SECONDS", "3"))

# realtime speech arrives in tiny pieces — join them per session after a pause
_buf_lock = threading.Lock()
_buffers: dict[str, list[str]] = {}
_timers: dict[str, threading.Timer] = {}

app = FastAPI(title="Smritaya — the witness for the verbal economy", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mode() -> dict:
    h = memory.health()
    return {"qdrant": h["qdrant"], "embedder": h["embedder"], "lyzr": agents.lyzr_kind(), "omi": omi.notify_kind(), "points": h["points"]}


def _public(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


# --------------------------------------------------------------- auth

def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return token or None


def _req_uid(authorization: str | None, fallback: str) -> str:
    """Authed calls operate on the account's uid, never a client-chosen one.
    Unauthed calls keep the legacy uid (device / demo) for Omi webhooks & seed."""
    user = auth.user_for_token(_bearer(authorization)) if authorization else None
    return user["uid"] if user else fallback


def _ledger_uid(omi_uid: str) -> str:
    """Omi appends its own uid to webhooks. If an account has linked that uid,
    store the deed in that account's ledger; otherwise keep the raw device uid."""
    u = auth.user_by_omi_uid(omi_uid)
    return u["uid"] if u else omi_uid


def _notify_uid(authorization: str | None, fallback: str) -> str:
    """Where to push the drafted nudge: the linked Omi uid if there is one, so
    the notification lands on the user's own app; else the ledger uid."""
    user = auth.user_for_token(_bearer(authorization)) if authorization else None
    if user:
        return user.get("omi_uid") or user["uid"]
    return fallback


def _auth_error(e: auth.AuthError) -> JSONResponse:
    return JSONResponse(status_code=e.code, content={"error": e.message})


@app.post("/auth/signup")
def signup(email: str = Body(..., embed=True), password: str = Body(..., embed=True)):
    try:
        user = auth.signup(email, password)
    except auth.AuthError as e:
        return _auth_error(e)
    return {"token": auth.create_session(user), "user": auth.public_user(user)}


@app.post("/auth/login")
def login(email: str = Body(..., embed=True), password: str = Body(..., embed=True)):
    try:
        user = auth.login(email, password)
    except auth.AuthError as e:
        return _auth_error(e)
    return {"token": auth.create_session(user), "user": auth.public_user(user)}


@app.post("/auth/logout")
def logout(authorization: str | None = Header(None)):
    auth.logout(_bearer(authorization))
    return {"ok": True}


@app.get("/auth/me")
def me(authorization: str | None = Header(None)):
    user = auth.user_for_token(_bearer(authorization))
    if not user:
        return JSONResponse(status_code=401, content={"error": "not signed in"})
    return {"user": auth.public_user(user)}


@app.post("/auth/forgot")
def forgot(email: str = Body(..., embed=True)):
    token = auth.request_reset(email)
    if not token:
        return {"ok": True, "reset_token": None, "message": "No account found for that email."}
    return {"ok": True, "reset_token": token, "message": "Reset link ready."}


@app.post("/auth/reset")
def reset(token: str = Body(..., embed=True), password: str = Body(..., embed=True)):
    try:
        auth.reset_password(token, password)
    except auth.AuthError as e:
        return _auth_error(e)
    return {"ok": True}


@app.post("/auth/omi")
def link_omi(omi_uid: str = Body("", embed=True), authorization: str | None = Header(None)):
    """Link (or clear) the account's Omi uid so webhooks map to it and
    notifications reach the user's own Omi app."""
    user = auth.user_for_token(_bearer(authorization))
    if not user:
        return JSONResponse(status_code=401, content={"error": "not signed in"})
    auth.set_omi_uid(user["id"], omi_uid)
    resp: dict = {"user": auth.public_user(auth.user_for_token(_bearer(authorization)))}
    moved = memory.remap_uid(omi_uid, user["uid"]) if omi_uid else 0
    if moved:
        resp["moved"] = moved
    return resp


# ------------------------------------------------------------------ omi

def _omi_ok(token: str | None) -> bool:
    """Guard the public webhook: only enforced when SMRITAYA_OMI_SECRET is set."""
    return not OMI_SECRET or token == OMI_SECRET


def _process_transcript(uid: str, text: str, source: str, speaker: str | None) -> int:
    text = _dedupe_stream((text or "").strip())
    if len(text) < MIN_CHARS:
        return 0
    deeds = agents.extract_deeds(text)
    for d in deeds:
        memory.record_deed(
            uid=uid,
            text=_dedupe_stream(d["quote"]),  # ponytail: extractor echoes Omi's interim repeats; collapse adjacent dupes, single chokepoint for every source
            counterparty=d["counterparty"],
            direction=d["direction"],
            amount=d["amount"],
            currency=d["currency"],
            due_ts=d["due_ts"],
            topic=d["topic"],
            source=source,
            speaker=speaker,
            extra=d.get("extra"),
        )
    return len(deeds)


def _dedupe_stream(text: str) -> str:
    """Omi's interim real-time transcript grows by repeating word fragments
    ('Ramesh Yadav Ramesh Yadav … 8 … 8000'). Collapse adjacent duplicates for
    the provisional text; the clean conversation webhook stays untouched."""
    words = text.split()
    out = []
    for w in words:
        if out and out[-1].lower() == w.lower():
            continue
        out.append(w)
    return " ".join(out)


def _conversation_text(payload: Any) -> tuple[str, str | None]:
    """Pull the spoken words out of any shape Omi's memory webhook sends."""
    transcript, speaker = "", None
    if isinstance(payload, list):
        transcript = " ".join(s.get("text", "") for s in payload if isinstance(s, dict))
        speaker = next((s.get("speaker") for s in payload if isinstance(s, dict) and s.get("speaker")), None)
    elif isinstance(payload, dict):
        node = payload
        for wrap in ("memory", "conversation"):
            if isinstance(node.get(wrap), dict):
                node = node[wrap]
        segments = node.get("segments") or node.get("transcript_segments") or []
        if isinstance(segments, list) and segments:
            transcript = " ".join(s.get("text", "") for s in segments if isinstance(s, dict))
            speaker = next((s.get("speaker") for s in segments if isinstance(s, dict) and s.get("speaker")), None)
        if not transcript:
            structured = node.get("structured") or payload.get("structured")
            if isinstance(structured, dict) and structured.get("overview"):
                transcript = str(structured["overview"])
        if not transcript and isinstance(node.get("transcript"), str):
            transcript = node["transcript"]
        if not transcript and isinstance(payload.get("text"), str):
            transcript = payload["text"]
    elif isinstance(payload, str):
        transcript = payload
    return transcript.strip(), speaker


@app.post("/omi/conversation")
def on_conversation(tasks: BackgroundTasks, uid: str = Query(DEMO_UID), token: str | None = Query(None), payload: Any = Body(...)):
    """Memory-creation trigger: fires when a conversation finishes. Answer 200 fast."""
    if not _omi_ok(token):
        return JSONResponse(status_code=403, content={"error": "forbidden"})
    uid = _ledger_uid(uid)
    # The completed-conversation text is the clean, canonical record: drop any
    # provisional realtime-flushed deed for this person from the last few minutes
    # so 'I spoke once' yields exactly one deed, not two.
    drafts = memory.strike_realtime_drafts(uid)
    if drafts:
        print(f"[omi] removed {drafts} provisional realtime draft deed(s) before storing the conversation deed")
    transcript, speaker = _conversation_text(payload)
    transcript = _dedupe_stream(transcript)  # ponytail: Omi final text also repeats interim fragments; adjacent-dup collapse, upgrade to diff-based merge if needed
    print(f"[omi] conversation uid={uid!r} keys={list(payload) if isinstance(payload, dict) else type(payload).__name__} len={len(transcript)} text={transcript[:160]!r}")

    tasks.add_task(_process_transcript, uid, transcript, "conversation", speaker)
    return {"status": "ok", "message": "Transcript queued for Lyzr deed extraction & Qdrant storage"}


def _flush_realtime(session: str, uid: str) -> None:
    """Join a session's buffered speech pieces and process them as one deed."""
    with _buf_lock:
        pieces = _buffers.pop(session, [])
        _timers.pop(session, None)
    text = " ".join(pieces).strip()
    if text:
        _process_transcript(uid, text, "realtime", None)


@app.post("/omi/realtime")
def on_realtime(tasks: BackgroundTasks, uid: str = Query(DEMO_UID), session_id: str = "", token: str | None = Query(None), payload: Any = Body(...)):
    """Real-time transcript batches while the user speaks. Kept light."""
    if not _omi_ok(token):
        return JSONResponse(status_code=403, content={"error": "forbidden"})
    uid = _ledger_uid(uid)
    transcript = ""
    if isinstance(payload, list):
        transcript = " ".join(s.get("text", "") for s in payload if isinstance(s, dict))
    elif isinstance(payload, dict):
        segments = payload.get("segments") or payload.get("transcript_segments") or []
        transcript = " ".join(s.get("text", "") for s in segments if isinstance(s, dict))
        if not transcript and "text" in payload:
            transcript = str(payload["text"])
    elif isinstance(payload, str):
        transcript = payload

    transcript = transcript.strip()
    transcript = _dedupe_stream(transcript)
    if not transcript:
        return {"status": "ok"}

    # Buffer per session and answer once the speaker pauses — no timer, no partial deeds.
    session = session_id or uid
    print(f"[omi] realtime uid={uid!r} session={session!r} nonzero_pieces={sum(1 for s in (payload if isinstance(payload, list) else (payload.get('segments') or payload.get('transcript_segments') or []) if isinstance(payload, dict) else []) if isinstance(s, dict) and s.get('text'))} len={len(transcript)} text={transcript[:160]!r}")
    # Omi's real-time webhook resends the FULL accumulated transcript on every burst, so
    # we replace (never append) and only ever keep the latest cumulative text — otherwise
    # the same words stack up ("Ramesh Ramesh ward Ramesh wardro ...").
    session = session_id or uid
    with _buf_lock:
        _buffers[session] = [transcript]
        old = _timers.get(session)
        if old:
            old.cancel()
        timer = threading.Timer(SILENCE_SECONDS, _flush_realtime, args=(session, uid))
        timer.daemon = True
        _timers[session] = timer
    timer.start()
    return {"status": "buffered"}


@app.post("/ingest")
def ingest_speech(
    uid: str = Body(DEMO_UID, embed=True),
    authorization: str | None = Header(None),
    transcript: str = Body(..., embed=True),
    speaker: str | None = Body(None, embed=True),
    source: str = Body("ambient_voice", embed=True),
):
    """Dynamically ingest spoken speech, run Lyzr Extractor agent, and record deeds in Qdrant."""
    uid = _req_uid(authorization, uid)
    deeds = agents.extract_deeds(transcript)
    saved = []
    for d in deeds:
        point_id = memory.record_deed(
            uid=uid,
            text=d["quote"],
            counterparty=d["counterparty"],
            direction=d["direction"],
            amount=d["amount"],
            currency=d["currency"],
            due_ts=d["due_ts"],
            topic=d["topic"],
            source=source,
            speaker=speaker,
            extra=d.get("extra"),
        )
        deed = memory.get_deed(point_id)
        if deed:
            saved.append(_public(deed))
    return {
        "status": "sworn",
        "count": len(saved),
        "deeds": saved,
        "transcript": transcript,
        "mode": _mode(),
    }


# ---------------------------------------------------------------- registry

@app.get("/health")
def health():
    return {"status": "sworn", "build": "4-dedupe-at-gate", "mode": _mode()}


def _landing_stats(uid: str) -> list[dict]:
    deeds = memory.list_deeds(uid)
    pending = [d for d in deeds if d["status"] == memory.STATUS_PENDING]
    overdue = [d for d in pending if d.get("overdue")]
    stake = sum((d.get("amount") or 0) for d in pending if d.get("direction") == "owed_to_me")
    chambers = len({d["counterparty"] for d in deeds})
    return [
        {"label": "words witnessed", "value": len(deeds)},
        {"label": "pending", "value": len(pending)},
        {"label": "overdue", "value": len(overdue), "tone": "broken"},
        {"label": "at stake", "value": stake, "format": "money", "tone": "gold"},
        {"label": "chambers", "value": chambers},
    ]


@app.get("/content")
def get_content(uid: str = DEMO_UID):
    """The landing page, content + copy, with live numbers from the record."""
    return {**content.LANDING, "stats": _landing_stats(uid)}


@app.get("/copy")
def get_copy():
    """The in-app interface copy — the frontend holds no hardcoded strings."""
    return content.APP


@app.get("/deeds")
def get_deeds(
    uid: str = DEMO_UID,
    authorization: str | None = Header(None),
    status: str | None = None,
    counterparty: str | None = None,
    overdue: bool | None = None,
):
    uid = _req_uid(authorization, uid)
    return {"deeds": [_public(d) for d in memory.list_deeds(uid, status, counterparty, overdue)], "mode": _mode()}


@app.post("/deeds")
def create_deed(
    uid: str = Body(DEMO_UID, embed=True),
    authorization: str | None = Header(None),
    text: str = Body(..., embed=True),
    counterparty: str = Body("Unnamed party", embed=True),
    direction: str = Body("owed_to_me", embed=True),
    amount: float | None = Body(None, embed=True),
    currency: str = Body("INR", embed=True),
    due_ts: float | None = Body(None, embed=True),
    topic: str = Body("general", embed=True),
    source: str = Body("manual", embed=True),
    status: str = Body(memory.STATUS_PENDING, embed=True),
):
    uid = _req_uid(authorization, uid)
    point_id = memory.record_deed(
        uid=uid, text=text, counterparty=counterparty, direction=direction,
        amount=amount, currency=currency, due_ts=due_ts, topic=topic,
        source=source, status=status,
    )
    d = memory.get_deed(point_id)
    return {"deed": _public(d) if d else None, "mode": _mode()}


@app.post("/remind")
def remind(
    deed_id: str = Body(..., embed=True),
    uid: str = Body(DEMO_UID, embed=True),
    authorization: str | None = Header(None),
):
    d = memory.get_deed(deed_id)
    if not d:
        return JSONResponse(status_code=404, content={"error": "no such deed"})
    memory.add_reminder(deed_id)
    d = memory.get_deed(deed_id)
    draft = _reminder_draft(d)
    # close the loop: push the drafted nudge back to the user's own Omi (no-op if unconfigured)
    receipt = omi.notify(_notify_uid(authorization, uid), draft)
    return {"deed": _public(d), "draft": draft, "notify": receipt}


def _reminder_draft(d: dict) -> str:
    due = datetime.fromtimestamp(d["due_ts"]).strftime("%d %b") if d.get("due_ts") else "the promised day"
    amt = f"{d['amount']:,.0f} {d['currency']}" if d.get("amount") else "what was agreed"
    return (
        f"Hi {d['counterparty']}, a small reminder — you said: \u201c{d['text']}\u201d — due {due} ({amt}). "
        f"Just let me know when to expect it. Thanks!"
    )


@app.post("/status")
def set_status(deed_id: str = Body(..., embed=True), status: str = Body(..., embed=True)):
    ok = memory.set_status(deed_id, status)
    return {"ok": ok, "deed": _public(memory.get_deed(deed_id)) if ok else None}


@app.get("/chamber/{counterparty}")
def get_chamber(counterparty: str, uid: str = DEMO_UID, authorization: str | None = Header(None)):
    uid = _req_uid(authorization, uid)
    c = memory.chamber(uid, counterparty)
    c["deeds"] = [_public(d) for d in c["deeds"]]
    return c


# ------------------------------------------------------------------ ask

@app.post("/ask")
def ask(
    uid: str = Body(DEMO_UID, embed=True),
    authorization: str | None = Header(None),
    question: str = Body(..., embed=True),
):
    uid = _req_uid(authorization, uid)
    context = memory.recall(uid, question)
    result = agents.advise(question, context)
    return {
        "answer": result["answer"],
        "agent": result["agent"],
        "context": [_public(c) for c in context],
        "mode": _mode(),
    }


# --------------------------------------------------------------- hearing

@app.post("/hearing")
def hearing(
    uid: str = Body(DEMO_UID, embed=True),
    authorization: str | None = Header(None),
    deed_id: str = Body(..., embed=True),
):
    uid = _req_uid(authorization, uid)
    deed = memory.get_deed(deed_id)
    if not deed:
        return JSONResponse(status_code=404, content={"error": "no such deed"})
    chamber = memory.chamber(uid, deed["counterparty"])
    memo = agents.draft_hearing(deed, chamber["trust"])
    evidence = [deed] + [d for d in chamber["deeds"] if d["id"] != deed_id][:4]
    if deed.get("overdue") or deed["status"] == memory.STATUS_BROKEN:
        memory.set_status(deed_id, memory.STATUS_CONTESTED)
    return {
        "acts": {
            "summons": {"narrative": memo.get("summons", "")},
            "evidence": [_public(e) for e in evidence],
            "pattern": {
                "trust": chamber["trust"],
                "narrative": memo.get("pattern_narrative", ""),
            },
            "memo": {
                "gentle": memo.get("gentle", ""),
                "firm": memo.get("firm", ""),
                "formal": memo.get("formal", ""),
                "advice": memo.get("advice", ""),
            },
        },
        "agent": memo.get("agent", "local-reasoner"),
        "mode": _mode(),
    }


# ---------------------------------------------------------------- privacy

@app.post("/forget")
def forget(
    deed_id: str | None = Body(None, embed=True),
    counterparty: str | None = Body(None, embed=True),
    uid: str | None = Body(None, embed=True),
    authorization: str | None = Header(None),
):
    """Strike from the record. The witness forgets on command."""
    uid_eff = _req_uid(authorization, uid or DEMO_UID)
    removed = memory.strike(point_id=deed_id, counterparty=counterparty, uid=uid_eff)
    return {"struck": removed}


# ------------------------------------------------------------------ static / dist
dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(dist_dir):
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Do not capture API routes
        if full_path.startswith("api/") or full_path.startswith("omi/") or full_path in {"health", "content", "copy", "deeds", "remind", "status", "ask", "hearing", "forget", "ingest"}:
            return JSONResponse(status_code=404, content={"error": "not found"})
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse(status_code=404, content={"error": "frontend dist not found"})
