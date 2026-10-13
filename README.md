# SMRITAYA — the witness for the verbal economy

> *"Remove any one — Omi, Qdrant, Lyzr — and there is no product."*

**Smritaya** (Sanskrit: *that which is remembered*) is an ambient AI witness that remembers every
verbal agreement made in your life — and fights for you when someone breaks their word.

India's informal economy runs on spoken promises: *"₹900 a day, paid Sunday." "Wardrobe by
Sunday, ₹8,000." "Return it next month, no tension."* When those words are broken — as millions
are, every day — the injured party has nothing. Not because the law ignores verbal contracts,
but because **no product could hear, remember, and argue.** Smritaya is the proof that this
stack can.

---

## The loop (one connected execution flow)

```
        ┌──────────────┐   webhooks    ┌────────────────────┐    upsert     ┌──────────────┐
        │     Omi      │ ────────────► │     Smritaya       │ ────────────► │    Qdrant    │
        │ (voice, app  │  transcripts  │  FastAPI backend   │  verbatim +   │  testimony   │
        │  or wearable)│               │  (the witness)     │  structured   │  collection  │
        └──────┬───────┘               └─────────┬──────────┘  facts        └──────┬───────┘
               │                                 │ retrieve top-k                  │
               │  notifications                  ▼                                 │
               └─────────────────────── ┌────────────────────┐ ◄──────────────────┘
                                        │    Lyzr agents     │
                                        │ Extractor · Advisor│
                                        │ Drafter            │
                                        └────────────────────┘
```

1. **Omi** sends transcripts to the backend through webhooks (memory-creation + real-time).
2. The **Extractor agent** (Lyzr) turns raw speech into *deeds* — `{who, quote, amount, due, topic}`.
3. Each deed is embedded and stored in **Qdrant** with structured payload facts.
4. Questions hit `/ask`: semantic **and** filtered retrieval (person, status, deadline) in one query.
5. The **Advisor agent** answers *only* from what was sworn, citing its snippets.
6. The **Drafter agent** convenes a *Hearing* for a broken word: a 4-act memo
   (Summons → Evidence → Pattern → escalation drafts, gentle → firm → formal).
7. Every step is observable — the UI shows the live mode of memory, embedder, and agents.

## The Testament Interface

No dashboards. No sidebars. The product is words, so the interface treats words as legal
artifacts:

- **The Stand** — one breathing ink-line; press `/` to question the witness.
- **The Ledger** — every promise as an ivory paper deed: the exact spoken words in large serif
  italic, metadata set as marginalia in the margins, status as rubber stamps.
- **The Chambers** — trust rendered as **wax seals**: intact, cracked, or broken. Each seal's
  blob is deterministically unique to the person.
- **The Hearing** — when a word breaks, the witness convenes a cinematic four-act trial and
  drafts the escalation ladder (copy-ready: gentle → firm → formal notice).
- **The Vault** — privacy as a legal right: "strike from the record" performs real deletion
  from Qdrant, per deed or per entire chamber.

## Stack mapping (mandatory: all three, genuinely)

| Layer | Usage |
|---|---|
| **Omi** | Developer-mode webhooks (`/omi/conversation`, `/omi/realtime`) ingest ambient speech; the notifications API closes the loop back to the user's phone. |
| **Qdrant** | The `testament` collection stores each deed's verbatim quote as a vector plus structured payload (`counterparty, amount, due_ts, status, topic, uid`). Retrieval combines cosine search with payload filters (datetime ranges, match) in a single query. Runs embedded/local for the privacy story. |
| **Lyzr** | Three specialized agents — Extractor, Advisor, Drafter — called via the Agent Studio chat API (`/v3/inference/chat/`), with a deterministic local reasoner as fallback so the loop never dies. Manager-style orchestration = the backend routing between agents per intent. |

## Run it

```bash
# 1. backend
cd backend
pip install -r requirements.txt
uvicorn app:app --port 8000

# 2. frontend
cd ../frontend
npm install
npm run dev               # http://localhost:5173  (dev, proxies /api -> :8000)
# or: npm run build       # then uvicorn serves frontend/dist automatically on :8000
```

Optional: copy `.env.example` → `.env` and add `LYZR_API_KEY` + `LYZR_AGENT_ID` to switch the
agents from the local reasoner to live Lyzr inference (the registry lamps in the UI show the
active mode). Qdrant runs embedded at `./qdrant_data` by default — zero setup; set
`QDRANT_MODE=remote` + `QDRANT_URL` for a server/cloud.

### Connect Omi (real device)

1. Omi app → Settings → Developer Mode.
2. Point the **memory-creation webhook** at `https://YOUR_TUNNEL/omi/conversation` and the
   **real-time transcript webhook** at `https://YOUR_TUNNEL/omi/realtime`
   (`ngrok http 8000` gives you the tunnel URL).
3. Speak: *"Ramesh, wardrobe by Sunday, eight thousand."* Watch it appear in the Ledger.

## Build track

**Privacy-First Knowledge Systems** — secure, local memory with granular, user-controlled
visibility (per-person chambers, verifiable strikes, per-user retrieval isolation), applied to
a problem a billion people know by heart.

## Submission checklist status

- [x] One connected loop: voice in → memory → agent reasoning → answers out
- [x] Architecture documentation + diagram (this file)
- [x] Multi-agent orchestration (Extractor / Advisor / Drafter + backend router)
- [x] Structured metadata + temporal retrieval (overdue, at-stake, per-person)
- [x] User control: strike from the record (deed-level and chamber-level)
- [x] Closed loop: reminder drafts + Omi notifications integration point
- [x] No API keys committed (`.env.example` provided)
- [x] Observable workflows: live registry lamps (memory / embedder / agents mode)
