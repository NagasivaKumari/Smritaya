"""The Lyzr agent layer — the reasoning bench of the witness.

Three specialized agents (run in Lyzr Agent Studio, called over REST):
  - EXTRACTOR : transcript  -> deeds (strict JSON)
  - ADVISOR   : context + question -> grounded answer, citing snippets
  - DRAFTER   : evidence -> hearing memo (gentle / firm / formal escalation ladder)

Every agent degrades gracefully: without LYZR_API_KEY the module switches to
deterministic local reasoning so the entire product loop stays alive and
demoable. The active mode is always reported to the UI (observable workflow).
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Any

import requests

CHAT_URL = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
TIMEOUT = 60


def build_extractor_prompt(base: datetime) -> str:
    """Dynamically generates Extractor prompt with current calendar anchors and Indian informal economy context."""
    today_str = base.strftime("%A, %d %B %Y")
    tomorrow = (base + timedelta(days=1)).strftime("%A, %d %B %Y")
    yesterday = (base - timedelta(days=1)).strftime("%A, %d %B %Y")

    return f"""You are the sworn Extractor Agent of Smritaya — the AI Witness for the verbal economy.
Today is {today_str}. (Yesterday was {yesterday}; tomorrow is {tomorrow}).

Your sacred duty:
Analyze the ambient speech TRANSCRIPT. Identify and extract every verbal promise, commitment, handshake agreement, loan, wage commitment, or informal undertaking.
India and the informal economy run on spoken words: carpenter work, contractor advances, salary promises, friend-to-friend loans, shop credit, deadlines ("wardrobe by Sunday", "₹8,000 on 15th", "return next month", "salary on Monday").
Understand English and Indian/Hinglish colloquial expressions (e.g., "kal bhej dunga", "parso", "agla somwar", "advance", "biyaj", "tankhwah", "hisaab", "lakh", "hazaar").

Classify direction strictly:
- "owed_to_me": The other party made a promise/commitment to the user (e.g., "I'll deliver the wardrobe by Sunday", "Ramesh said he will return Rs 5,000").
- "i_owe": The user made a promise to the other party (e.g., "I will pay you tomorrow", "Main kal transfer kar dunga").

Resolve relative dates strictly based on today ({today_str}):
- "tomorrow" -> {tomorrow}
- "by Sunday" / "next week" / "month end" -> calculate the exact ISO 8601 date string (YYYY-MM-DD).

Return ONLY a valid JSON object (no markdown code fence, no conversational chatter):
{{
  "deeds": [
    {{
      "counterparty": string (name of the person or party involved, or "Unnamed party"),
      "direction": "owed_to_me" or "i_owe",
      "quote": string (the exact spoken commitment words, verbatim),
      "amount": number or null (numeric value only, e.g. 8000 for ₹8,000 or 50000 for 50k),
      "currency": "INR",
      "due": "YYYY-MM-DD" or null,
      "topic": string (concise topic: "wages", "carpentry", "loan", "rent", "freelance", "delivery", "repair"),
      "confidence": number between 0.1 and 1.0
    }}
  ]
}}
If no commitments or agreements are present, return {{"deeds": []}}."""


def build_advisor_prompt(base: datetime) -> str:
    """Dynamically generates Advisor prompt as a sworn witness testifying strictly from recorded testament."""
    today_str = base.strftime("%A, %d %B %Y")
    return f"""You are the Advisor Agent of Smritaya — the sworn AI Witness in the Court of Verbal Agreements.
Today's date is {today_str}.

You are presented with sworn testament in CONTEXT (verbatim deeds retrieved from persistent vector memory) and a user's QUESTION.

Rules of Testimony:
1. Grounded Witness: Testify ONLY from what is explicitly recorded in CONTEXT. If the answer is not in the record, state clearly: "The witness holds no memory of this matter. Nothing has been sworn into the record."
2. Verbatim Quotation: Always quote the exact spoken words in quotation marks when referencing an agreement.
3. Stakes and Deadlines: State the counterparty name, exact amount/currency, and due date. Calculate whether it is currently overdue, upcoming, or honored based on today ({today_str}).
4. Tone: Solemn, precise, calm, and legally grounded. You are testifying under oath, not chatting."""


def build_drafter_prompt(base: datetime) -> str:
    """Dynamically generates Drafter prompt for convening a 4-act hearing and legal escalation ladder."""
    today_str = base.strftime("%A, %d %B %Y")
    return f"""You are the Drafter Agent of Smritaya — the legal counsel and scribe for the verbal economy.
Today is {today_str}.

You receive EVIDENCE detailing a broken or disputed verbal promise (the verbatim deed, timestamps, counterparty history, and trust record).
Under the Indian Contract Act, 1872 (Section 10), oral agreements are legally valid and enforceable when made by free consent with lawful consideration. Smritaya provides the contemporaneous witness record.

Convene a 4-Act Hearing Memo. Return ONLY a valid JSON object (no markdown fence, no markdown ticks, no extra text):
{{
  "summons": string (2-3 solemn sentences framing the dispute: who spoke the word, what was promised, when it was breached, and why the hearing is convened),
  "gentle": string (First escalation: a warm, polite WhatsApp/SMS reminder quoting the verbatim words and asking for an updated date),
  "firm": string (Second escalation: an assertive message citing the exact quote, overdue duration, prior reminders, and demanding fulfillment this week),
  "formal": string (Final legal notice: formal demand citing oral contract enforceability under Indian law, timestamped witness testimony, 7-day cure period, and notice of legal proceedings upon default),
  "advice": string (Practical tactical advice for the user on how to approach this specific party given their trust record),
  "pattern_narrative": string (1-2 sentences summarizing the counterparty's reputation and credibility track record)
}}"""


def _cfg() -> dict:
    return {
        "key": os.environ.get("LYZR_API_KEY", ""),
        "extractor": os.environ.get("LYZR_EXTRACTOR_AGENT_ID", os.environ.get("LYZR_AGENT_ID", "")),
        "advisor": os.environ.get("LYZR_ADVISOR_AGENT_ID", os.environ.get("LYZR_AGENT_ID", "")),
        "drafter": os.environ.get("LYZR_DRAFTER_AGENT_ID", os.environ.get("LYZR_AGENT_ID", "")),
        "user_id": os.environ.get("LYZR_USER_ID", "founder@smritaya.app"),
    }


def lyzr_kind() -> str:
    cfg = _cfg()
    return "lyzr/live" if (cfg["key"] and cfg["extractor"]) else "local-reasoner"


def _call(agent_id: str, system_hint: str, message: str) -> str:
    cfg = _cfg()
    if not (cfg["key"] and agent_id):
        raise RuntimeError("lyzr-not-configured")

    # Combine dynamic system instructions directly into the message payload
    # so Lyzr executes with full dynamic instructions even if using a generic agent in Studio.
    full_message = f"""[SYSTEM DIRECTIVE & SCHEMA]
{system_hint}

[INPUT DATA]
{message}"""

    # ponytail: fresh session per call — Lyzr keeps per-session history, so a fixed
    # session id would leak prior transcripts/questions into the next extraction.
    task_session = f"smritaya-{agent_id}-{uuid.uuid4().hex[:10]}"

    r = requests.post(
        CHAT_URL,
        headers={"Content-Type": "application/json", "x-api-key": cfg["key"]},
        json={
            "user_id": cfg["user_id"],
            "agent_id": agent_id,
            "session_id": task_session,
            "message": full_message,
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json().get("response", "")


def _extract_json(text: str) -> Any:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("["), text.rfind("]")
    s2, e2 = text.find("{"), text.rfind("}")
    if start != -1 and (s2 == -1 or start < s2):
        return json.loads(text[start : end + 1])
    if s2 != -1:
        return json.loads(text[s2 : e2 + 1])
    raise ValueError("no json in agent response")


# --------------------------------------------------- dynamic field mapping
# ponytail: users name their Studio schema fields however they like. Instead of a
# fixed contract we resolve each canonical field from the first matching alias.
# Add a name to a tuple here and it's supported with no other code change.
_FIELD_ALIASES = {
    "counterparty": ("counterparty", "party", "person", "name", "who", "payer", "from"),
    "direction": ("direction", "owes", "owing", "obligation"),
    "quote": ("quote", "text", "words", "promise", "verbatim", "statement", "content", "message"),
    "amount": ("amount", "value", "money", "sum", "rupees", "price", "total"),
    "currency": ("currency", "ccy"),
    "due": ("due", "due_date", "deadline", "date", "due_at", "by", "when"),
    "topic": ("topic", "category", "subject", "type", "kind"),
    "confidence": ("confidence", "score", "certainty"),
    "summons": ("summons", "opening", "act1", "act_i"),
    "gentle": ("gentle", "polite", "reminder", "soft"),
    "firm": ("firm", "assertive", "demand"),
    "formal": ("formal", "legal", "legal_notice", "notice"),
    "advice": ("advice", "guidance", "tactics"),
    "pattern_narrative": ("pattern_narrative", "pattern", "reputation", "credibility"),
}
_DEED_WRAPPERS = ("deeds", "commitments", "promises", "items", "data", "results", "agreements", "records")
_MEMO_WRAPPERS = ("memo", "hearing_memo", "hearing", "data", "result", "output")
_MEMO_FIELDS = ("summons", "gentle", "firm", "formal", "advice", "pattern_narrative")


def _resolve(d: dict, field: str, default=None):
    """Return (matched_key, value) for the first present alias of a field."""
    for k in _FIELD_ALIASES.get(field, (field,)):
        v = d.get(k)
        if v not in (None, ""):
            return k, v
    return None, default


def _pick(d: dict, field: str, default=None):
    return _resolve(d, field, default)[1]


def _as_pairs(v) -> dict:
    """Normalize a details bag: a dict, or a list of {key,value} objects (strict-schema form)."""
    if isinstance(v, dict):
        return dict(v)
    out: dict = {}
    if isinstance(v, list):
        for item in v:
            if isinstance(item, dict):
                k = item.get("key") or item.get("name")
                if k is not None:
                    out[str(k)] = item.get("value", item)
                else:
                    out.update(item)
    return out


def _to_float(v):
    if v in (None, ""):
        return None
    try:
        return float(re.sub(r"[^\d.\-]", "", str(v)) or 0)
    except (TypeError, ValueError):
        return None


def _to_ts(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s)
    try:
        return datetime.fromisoformat(s[:10]).timestamp()
    except ValueError:
        return None


def _map_deed(d: dict) -> dict:
    used: set[str] = set()

    def take(field, default=None):
        k, v = _resolve(d, field, default)
        if k is not None:
            used.add(k)
        return v

    direction = str(take("direction") or "").strip().lower().replace("-", "_").replace(" ", "_")
    try:
        conf = float(take("confidence") or 0.8)
    except (TypeError, ValueError):
        conf = 0.8
    deed = {
        "counterparty": str(take("counterparty") or "Unnamed party").strip() or "Unnamed party",
        "direction": "i_owe" if direction in {"i_owe", "owe", "self", "user_owes"} else "owed_to_me",
        "quote": str(take("quote") or "").strip(),
        "amount": _to_float(take("amount")),
        "currency": str(take("currency") or "INR"),
        "due_ts": _to_ts(take("due")),
        "topic": (str(take("topic") or "general").strip().lower() or "general"),
        "confidence": conf,
    }
    # ponytail: anything the user's schema invents beyond the canonical fields is
    # kept verbatim in "extra" and persisted — nothing is silently dropped.
    extra = {k: v for k, v in d.items() if k not in used}
    for bag in ("details", "data", "extra", "attributes", "metadata"):  # flatten a catch-all bag
        inner = extra.pop(bag, None)
        if inner is not None:
            extra = {**_as_pairs(inner), **extra}
    deed["extra"] = extra
    return deed


def _unwrap_deeds(out: Any) -> list:
    if isinstance(out, list):
        return out
    if isinstance(out, dict):
        for k in _DEED_WRAPPERS:
            if isinstance(out.get(k), list):
                return out[k]
        if _pick(out, "quote"):
            return [out]
    return []


def _normalize_memo(out: Any) -> dict | None:
    if not isinstance(out, dict):
        return None
    for k in _MEMO_WRAPPERS:
        if isinstance(out.get(k), dict):
            out = out[k]
            break
    memo = {f: str(_pick(out, f) or "") for f in _MEMO_FIELDS}
    return memo if any(memo.values()) else None


# ------------------------------------------------------------- extractor

_MONEY = re.compile(
    r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)"
    r"|([\d,]+(?:\.\d+)?)\s*(?:₹|rs\.?|rupees)"
    r"|(\d{1,3}(?:,\d{2,3})+)",  # ponytail: bare Indian-grouped amount, e.g. "25,000"
    re.I,
)
_ONES = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90,
}
_MULT = {"thousand": 1000, "hazaar": 1000, "hazar": 1000, "k": 1000, "lakh": 100000, "lac": 100000}
_WORDS_MONEY = re.compile(
    r"\b((?:(?:" + "|".join(_ONES) + r"|and|\s|-)+?)"
    r"(?:" + "|".join(_MULT) + r"))\b",
    re.I,
)


def _words_to_num(s: str) -> int:
    total = cur = 0
    for w in re.split(r"[\s-]+", s.lower()):
        if w in _ONES:
            cur += _ONES[w]
        elif w in _MULT:
            cur = (cur or 1) * _MULT[w]
            total += cur
            cur = 0
    return total + cur


_PROMISE = re.compile(
    r"\b(i will|i'll|you will|you'll|he will|she will|they will|we will|we'll|"
    r"will you|promise|by [a-z]+day|next week|next month|tomorrow|pay|give|bring|deliver|"
    r"finish|complete|return|send|fix|come|"
    # ponytail: Hinglish future-tense markers — the local reasoner's only blind spot
    r"dega|degi|dunga|dungi|denge|karunga|karega|kar\s+de)\b",
    re.I,
)


def _local_due(text: str, base: datetime) -> float | None:
    t = text.lower()
    if "day after" in t:
        return (base + timedelta(days=2)).timestamp()
    if "tomorrow" in t:
        return (base + timedelta(days=1)).timestamp()
    if "next week" in t:
        return (base + timedelta(days=7)).timestamp()
    if "next month" in t:
        nxt = base.replace(day=28) + timedelta(days=4)
        return nxt.replace(day=1).timestamp()
    if "month end" in t or "end of month" in t:
        nxt = base.replace(day=28) + timedelta(days=4)
        return nxt.replace(day=1).timestamp()
    # scan the next 7 real days and match their weekday names — no lookup table
    for i in range(1, 8):
        day = base + timedelta(days=i)
        if re.search(rf"\b{day.strftime('%A').lower()}\b", t):
            return day.timestamp()
    m = re.search(r"(\d{1,2})\s*(?:/|-)\s*(\d{1,2})", t)
    if m:
        try:
            d = base.replace(day=int(m.group(1)), month=int(m.group(2)))
            if d < base:
                d = d.replace(year=d.year + 1)
            return d.timestamp()
        except ValueError:
            pass
    return None


def _collapse_repeats(text: str) -> str:
    """Collapse Omi-style cumulative captions: consecutive duplicate words + doubled phrases."""
    text = re.sub(r"(?i)\b(\w+)(?:\s+\1\b)+", r"\1", text.strip())
    words = text.split()
    changed = True
    while changed:  # e.g. "sofa by Friday ... sofa by Friday" -> one
        changed = False
        for size in range(len(words) // 2, 0, -1):
            a, b = words[-2 * size:-size], words[-size:]
            if [w.lower() for w in a] == [w.lower() for w in b]:
                del words[-size:]
                changed = True
                break
    return " ".join(words)


def extract_deeds(transcript: str, base: datetime | None = None) -> list[dict]:
    """Extractor agent (Lyzr live with dynamic prompt, deterministic reasoner as fallback)."""
    transcript = _collapse_repeats(transcript)
    base = base or datetime.now()
    cfg = _cfg()
    if cfg["key"] and cfg["extractor"]:
        try:
            prompt = build_extractor_prompt(base)
            raw = _call(
                cfg["extractor"],
                prompt,
                f"TRANSCRIPT TO EXTRACT FROM:\n{transcript}",
            )
            out = _extract_json(raw)
            deeds = [_map_deed(d) for d in _unwrap_deeds(out) if isinstance(d, dict)]
            deeds = [d for d in deeds if d["quote"]]
            if deeds:
                return deeds
        except Exception:
            pass
    return _local_extract(transcript, base)


def _local_extract(transcript: str, base: datetime) -> list[dict]:
    """Deterministic fallback: sentence-level promise detection."""
    sentences = re.split(r"(?<=[.!?])\s+|\n+", transcript)
    found: list[dict] = []
    for s in sentences:
        s = s.strip()
        if len(s) < 12 or not _PROMISE.search(s):
            continue
        amount = None
        m = _MONEY.search(s)
        if m:
            amount = float(next(g for g in m.groups() if g).replace(",", ""))
        else:
            wm = _WORDS_MONEY.search(s)
            if wm:
                amount = float(_words_to_num(wm.group(1)))
        name = "Unnamed party"
        for candidate in re.findall(r"\b[A-Z][a-z]{2,}\b", s):
            if candidate.lower() not in {"i", "will", "the", "monday", "sunday", "saturday"}:
                name = candidate
                break
        found.append(
            {
                "counterparty": name,
                "direction": "owed_to_me",
                "quote": s,
                "amount": amount,
                "currency": "INR",
                "due_ts": _local_due(s, base),
                "topic": "general",
                "confidence": 0.6,
            }
        )
    return found


# ---------------------------------------------------------------- advisor

def advise(question: str, context: list[dict], base: datetime | None = None) -> dict:
    base = base or datetime.now()
    cfg = _cfg()
    ctx = "\n".join(
        f"- [{d['counterparty']}] \"{d['text']}\" (status: {d['status']}"
        + (f", due: {datetime.fromtimestamp(d['due_ts']).date()}" if d.get("due_ts") else "")
        + (f", amount: {d['amount']} {d['currency']}" if d.get("amount") else "")
        + ")"
        for d in context
    ) or "none"
    if cfg["key"] and cfg["advisor"]:
        try:
            prompt = build_advisor_prompt(base)
            answer = _call(cfg["advisor"], prompt, f"CONTEXT (SWORN MEMORIES):\n{ctx}\n\nQUESTION FROM USER:\n{question}")
            return {"answer": answer, "agent": "lyzr/live"}
        except Exception:
            pass
    return {"answer": _local_advise(question, context), "agent": "local-reasoner"}


def _local_advise(question: str, context: list[dict]) -> str:
    if not context:
        return "Nothing in the record speaks to that. The witness holds no such memory."
    lines = []
    q = question.lower()
    scored = sorted(context, key=lambda d: d["ts"], reverse=True)
    if "overdue" in q or "due" in q or "pending" in q:
        scored = [d for d in context if d.get("overdue")] or scored
    for d in scored[:3]:
        when = datetime.fromtimestamp(d["ts"]).strftime("%d %b")
        due = datetime.fromtimestamp(d["due_ts"]).strftime("%d %b") if d.get("due_ts") else "no date set"
        lines.append(
            f"On {when}, {d['counterparty']} was recorded: \u201c{d['text']}\u201d — due {due}, status {d['status']}"
            + (f", {d['amount']} {d['currency']} at stake" if d.get("amount") else "")
            + (" — now OVERDUE" if d.get("overdue") else "")
        )
    return "\n".join(lines)


# ---------------------------------------------------------------- drafter

def draft_hearing(deed: dict, history: dict, base: datetime | None = None) -> dict:
    base = base or datetime.now()
    cfg = _cfg()
    evidence = {
        "deed": {
            "quote": deed["text"],
            "counterparty": deed["counterparty"],
            "amount": deed.get("amount"),
            "currency": deed.get("currency", "INR"),
            "recorded_at": datetime.fromtimestamp(deed["ts"]).strftime("%d %B %Y"),
            "due_at": datetime.fromtimestamp(deed["due_ts"]).strftime("%d %B %Y") if deed.get("due_ts") else None,
            "reminders_sent": len(deed.get("reminders") or []),
            "source": deed.get("source"),
        },
        "history": history,
    }
    if cfg["key"] and cfg["drafter"]:
        try:
            prompt = build_drafter_prompt(base)
            raw = _call(cfg["drafter"], prompt, "EVIDENCE TO DRAFT HEARING FOR:\n" + json.dumps(evidence, indent=2))
            memo = _normalize_memo(_extract_json(raw))
            if memo:
                memo["agent"] = "lyzr/live"
                return memo
        except Exception:
            pass
    return _local_draft(evidence)


def _local_draft(evidence: dict) -> dict:
    d = evidence["deed"]
    name = d["counterparty"]
    amount = f"{d['amount']:,.0f} {d['currency']}" if d.get("amount") else "the agreed amount"
    due = d.get("due_at") or "the promised date"
    recorded = d["recorded_at"]
    reminders = d["reminders_sent"]
    gentle = (
        f"Hi {name}, hope you're well — just remembering our agreement from {recorded}: \u201c{d['quote']}\u201d. "
        f"It was due {due}. Could you let me know when to expect it?"
    )
    firm = (
        f"{name}, following up again on our agreement of {recorded}: \u201c{d['quote']}\u201d. "
        f"The date agreed was {due}, and {reminders} reminder(s) have already been sent. "
        f"I'm counting on you to honour this — {amount} — by this week. Please confirm a firm date."
    )
    formal = (
        f"To {name}.\n\n"
        f"This is a formal record of a verbal agreement made on {recorded}, witnessed and archived: \u201c{d['quote']}\u201d. "
        f"The obligation fell due on {due} and remains unmet despite {reminders} prior reminder(s). "
        f"You are requested to fulfil the undertaking ({amount}) within seven (7) days of this notice, "
        f"failing which this record, with its verbatim transcript and timestamps, will be placed before "
        f"the appropriate forum for recovery."
    )
    h = evidence.get("history") or {}
    seal = h.get("seal", "untested")
    pattern = (
        f"{name} has kept {h.get('kept', 0)} and broken {h.get('broken', 0)} recorded promises "
        f"(seal: {seal})." if h else f"{name} has no prior record — this would be the first broken word."
    )
    return {
        "summons": (
            f"On {recorded}, {name} gave their word: \u201c{d['quote']}\u201d. "
            f"The date came and passed. This hearing assembles the record — the exact words, "
            f"the dates, and the pattern — and drafts what may be sent."
        ),
        "gentle": gentle,
        "firm": firm,
        "formal": formal,
        "advice": (
            "Send the gentle note first; keep every reply. If {n} stays silent for three days, "
            "escalate to the firm message, and keep the formal notice as your last resort."
        ).replace("{n}", name),
        "pattern_narrative": pattern,
        "agent": "local-reasoner",
    }
