"""Qdrant memory layer + embeddings for Smritaya.

Every spoken moment is stored as a point in the "testament" collection:
  - verbatim quote as text + vector (semantic retrieval: "what did we agree about the wardrobe")
  - structured facts in payload: counterparty, amount, due_ts, status, topic
    (filtered retrieval: "overdue promises from Ramesh about repair")
Both in one query — that is the witness's memory.

Runs in two modes:
  - QDRANT_MODE=remote  -> Qdrant server / cloud (QDRANT_URL, optional QDRANT_API_KEY)
  - QDRANT_MODE=local   -> embedded on-disk store at QDRANT_PATH (default ./qdrant_data), zero setup
"""

from __future__ import annotations

import math
import os
import time
import uuid
from typing import Any

COLLECTION = "testament"
DIM = 384

# Matches scoring below this are "not relevant" — stops the Advisor answering
# from unrelated deeds. bge-small-en-v1.5 scores unrelated text ~0.45 and real
# matches ~0.6+, so 0.55 separates them. Override with SMRITAYA_SCORE_THRESHOLD.
SCORE_THRESHOLD = float(os.environ.get("SMRITAYA_SCORE_THRESHOLD", "0.55"))

_state: dict[str, Any] = {}


def _client():
    if "qdrant" in _state:
        return _state["qdrant"]
    from qdrant_client import QdrantClient

    mode = os.environ.get("QDRANT_MODE", "local").strip().lower()
    if mode == "remote":
        url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        api_key = os.environ.get("QDRANT_API_KEY") or None
        qdrant = QdrantClient(url=url, api_key=api_key, timeout=15)
    else:
        qdrant = QdrantClient(path=os.environ.get("QDRANT_PATH", "./qdrant_data"))
    _state["qdrant"] = qdrant
    _ensure_collection(qdrant)
    _state["mode"] = mode
    return qdrant


def _ensure_collection(qdrant) -> None:
    from qdrant_client.models import Distance, VectorParams

    if not qdrant.collection_exists(COLLECTION):
        qdrant.create_collection(
            COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )


# ---------------------------------------------------------------- embeddings

_hash_vocab: dict[str, int] = {}


def _fallback_embed(text: str) -> list[float]:
    """Deterministic hashed bag-of-subwords vector. Keeps the whole loop runnable
    with zero downloads; semantic quality comes from fastembed when available."""
    import hashlib

    vec = [0.0] * DIM
    words = [w.strip(".,!?;:()[]\"'").lower() for w in text.split()]
    grams: list[str] = []
    for w in words:
        if w:
            grams.append(w)
            for i in range(len(w) - 2):
                grams.append(w[i : i + 3])
    for g in grams:
        h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16)
        idx = h % DIM
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _fastembed():
    if "embedder" in _state:
        return _state["embedder"]
    try:
        from fastembed import TextEmbedding

        _state["embedder"] = TextEmbedding("BAAI/bge-small-en-v1.5")  # 384 dims
        _state["embedder_kind"] = "fastembed/bge-small-en-v1.5"
    except Exception:
        _state["embedder"] = None
        _state["embedder_kind"] = "fallback-hash"
    return _state["embedder"]


def embed(text: str) -> list[float]:
    embedder = _fastembed()
    if embedder is None:
        return _fallback_embed(text)
    try:
        return next(iter(embedder.embed([text]))).tolist()
    except Exception:
        # model weights unavailable mid-session — degrade instead of dying
        _state["embedder"] = None
        _state["embedder_kind"] = "fallback-hash"
        return _fallback_embed(text)


def embedder_kind() -> str:
    _fastembed()
    return _state.get("embedder_kind", "fallback-hash")


def qdrant_kind() -> str:
    _client()
    return f"{_state.get('mode', 'local')}"


# ------------------------------------------------------------------- writes

STATUS_PENDING = "pending"
STATUS_KEPT = "kept"
STATUS_BROKEN = "broken"
STATUS_CONTESTED = "contested"


def record_deed(
    uid: str,
    text: str,
    counterparty: str,
    direction: str = "owed_to_me",
    amount: float | None = None,
    currency: str = "INR",
    due_ts: float | None = None,
    status: str = STATUS_PENDING,
    topic: str = "general",
    source: str = "manual",
    speaker: str | None = None,
    ts: float | None = None,
    extra: dict | None = None,
) -> str:
    from qdrant_client.models import PointStruct

    point_id = str(uuid.uuid4())
    qdrant = _client()
    qdrant.upsert(
        COLLECTION,
        points=[
            PointStruct(
                id=point_id,
                vector=embed(f"{counterparty} {topic} {text}"),
                payload={
                    "kind": "deed",
                    "uid": uid,
                    "text": text,
                    "counterparty": counterparty,
                    "direction": direction,
                    "amount": amount,
                    "currency": currency,
                    "due_ts": due_ts,
                    "status": status,
                    "topic": topic,
                    "source": source,
                    "speaker": speaker,
                    "ts": ts or time.time(),
                    "reminders": [],
                    "extra": extra or {},
                },
            )
        ],
    )
    return point_id


def add_reminder(point_id: str) -> bool:
    from qdrant_client.models import PointIdsList

    qdrant = _client()
    try:
        points = qdrant.retrieve(COLLECTION, ids=[point_id], with_payload=True)
    except Exception:
        return False
    if not points:
        return False
    payload = points[0].payload or {}
    payload.setdefault("reminders", []).append(time.time())
    qdrant.set_payload(COLLECTION, payload={"reminders": payload["reminders"]}, points=[point_id])
    return True


def set_status(point_id: str, status: str) -> bool:
    qdrant = _client()
    try:
        qdrant.set_payload(COLLECTION, payload={"status": status}, points=[point_id])
        return True
    except Exception:
        return False


def strike(point_id: str | None = None, counterparty: str | None = None, uid: str | None = None) -> int:
    """'Strike from the record' — the privacy right to be forgotten."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue, PointIdsList

    qdrant = _client()
    if point_id:
        try:
            qdrant.delete(COLLECTION, points_selector=PointIdsList(points=[point_id]))
            return 1
        except Exception:
            return 0
    must = []
    if counterparty:
        must.append(FieldCondition(key="counterparty", match=MatchValue(value=counterparty)))
    if uid:
        must.append(FieldCondition(key="uid", match=MatchValue(value=uid)))
    if not must:
        return 0
    before = qdrant.count(COLLECTION, exact=True).count
    qdrant.delete(COLLECTION, points_selector=Filter(must=must))
    after = qdrant.count(COLLECTION, exact=True).count
    return max(before - after, 0)


def remap_uid(old_uid: str, new_uid: str) -> int:
    """Move every stored deed from one uid to another — used when a user links
    their Omi id so previously-recorded conversations land in the account."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    qdrant = _client()
    if not old_uid or old_uid == new_uid:
        return 0
    try:
        hits = qdrant.scroll(
            COLLECTION,
            scroll_filter=Filter(must=[FieldCondition(key="uid", match=MatchValue(value=old_uid))]),
            limit=10000,
            with_payload=False,
        )[0]
    except Exception:
        return 0
    ids = [p.id for p in hits]
    if not ids:
        return 0
    qdrant.set_payload(COLLECTION, payload={"uid": new_uid}, points=ids)
    return len(ids)


# -------------------------------------------------------------------- reads

def _overdue(payload: dict) -> bool:
    due = payload.get("due_ts")
    return (
        payload.get("status") == STATUS_PENDING
        and due is not None
        and due < time.time()
    )


def list_deeds(
    uid: str,
    status: str | None = None,
    counterparty: str | None = None,
    overdue: bool | None = None,
) -> list[dict]:
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    must = [FieldCondition(key="kind", match=MatchValue(value="deed"))]
    if uid:
        must.append(FieldCondition(key="uid", match=MatchValue(value=uid)))
    if status:
        must.append(FieldCondition(key="status", match=MatchValue(value=status)))
    if counterparty:
        must.append(FieldCondition(key="counterparty", match=MatchValue(value=counterparty)))
    hits = _client().scroll(
        COLLECTION,
        scroll_filter=Filter(must=must),
        limit=256,
        with_payload=True,
    )[0]
    deeds = [_present(h.payload, h.id) for h in hits]
    if overdue is not None:
        deeds = [d for d in deeds if _overdue(d["_payload"])] if overdue else [d for d in deeds if not _overdue(d["_payload"])]
    deeds.sort(key=lambda d: d["ts"], reverse=True)
    return deeds


def get_deed(point_id: str) -> dict | None:
    pts = _client().retrieve(COLLECTION, ids=[point_id], with_payload=True)
    if not pts:
        return None
    return _present(pts[0].payload, pts[0].id)


def recall(uid: str, question: str, k: int = 5, score_threshold: float | None = None) -> list[dict]:
    """Semantic + structured recall in one query — the heart of the witness."""
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    must = [
        FieldCondition(key="kind", match=MatchValue(value="deed")),
        FieldCondition(key="uid", match=MatchValue(value=uid)),
    ]
    query_vec = embed(question)
    if score_threshold is None:
        # ponytail: the hashed fallback embedder scores far lower than bge-small,
        # so use a floor that keeps real matches but still drops nonsense.
        score_threshold = 0.05 if _state.get("embedder_kind") == "fallback-hash" else SCORE_THRESHOLD
    res = _client().query_points(
        COLLECTION,
        query=query_vec,
        query_filter=Filter(must=must),
        limit=k,
        score_threshold=score_threshold,
        with_payload=True,
    )
    return [_present(p.payload, p.id) for p in res.points]


def overdue_since(uid: str, days: int = 14) -> list[dict]:
    from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

    must = [
        FieldCondition(key="kind", match=MatchValue(value="deed")),
        FieldCondition(key="uid", match=MatchValue(value=uid)),
        FieldCondition(key="status", match=MatchValue(value=STATUS_PENDING)),
        FieldCondition(key="due_ts", range=Range(lt=time.time() - days * 86400)),
    ]
    hits = _client().scroll(COLLECTION, scroll_filter=Filter(must=must), limit=100, with_payload=True)[0]
    return [_present(h.payload, h.id) for h in hits]


def chamber(uid: str, counterparty: str) -> dict:
    """The dossier: everything sworn about one counterparty + their wax seal."""
    deeds = list_deeds(uid=uid, counterparty=counterparty)
    kept = [d for d in deeds if d["status"] == STATUS_KEPT]
    broken = [d for d in deeds if d["status"] == STATUS_BROKEN]
    pending = [d for d in deeds if d["status"] == STATUS_PENDING]
    contested = [d for d in deeds if d["status"] == STATUS_CONTESTED]
    decided = len(kept) + len(broken)
    if decided == 0:
        score, seal = None, "untested"
    else:
        score = len(kept) / decided
        seal = "intact" if score >= 0.75 else ("cracked" if score >= 0.4 else "broken")
    at_stake = sum((d["amount"] or 0) for d in pending if d["direction"] == "owed_to_me")
    return {
        "counterparty": counterparty,
        "deeds": deeds,
        "trust": {
            "score": score,
            "seal": seal,
            "kept": len(kept),
            "broken": len(broken),
            "pending": len(pending),
            "contested": len(contested),
            "at_stake": at_stake,
            "currency": "INR",
        },
    }


def _present(payload: dict | None, point_id: str) -> dict:
    p = dict(payload or {})
    due = p.get("due_ts")
    p_public = {
        "id": point_id,
        "text": p.get("text", ""),
        "counterparty": p.get("counterparty", "Unnamed party"),
        "direction": p.get("direction", "owed_to_me"),
        "amount": p.get("amount"),
        "currency": p.get("currency", "INR"),
        "due_ts": due,
        "status": p.get("status", STATUS_PENDING),
        "overdue": _overdue(p),
        "topic": p.get("topic", "general"),
        "source": p.get("source", "manual"),
        "speaker": p.get("speaker"),
        "ts": p.get("ts", 0),
        "reminders": p.get("reminders", []),
        "extra": p.get("extra", {}),
        "_payload": p,
    }
    return p_public


def health() -> dict:
    try:
        count = _client().count(COLLECTION, exact=True).count
    except Exception:
        count = -1
    return {
        "qdrant": qdrant_kind(),
        "embedder": embedder_kind(),
        "points": count,
    }
