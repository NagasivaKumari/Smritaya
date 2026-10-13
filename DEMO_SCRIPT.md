# Smritaya — Demo Video Script (& ~2:30)

**Track:** Privacy-First Knowledge Systems · **Hackathon:** Stop Prompting, Solo Agents (AI House × HiDevs)
**Stack:** Omi → FastAPI → Lyzr (extraction/advisor) → Qdrant (private vector memory) → React

## Prep checklist (before recording)
- [ ] Backend running: `python -m uvicorn app:app --host 127.0.0.1 --port 8000`
- [ ] Frontend running: `npm run dev` in `frontend/` → open `http://localhost:5173`
- [ ] ngrok tunnel live, and **saved in Omi Developer Settings** (Conversation Events + Real-Time Transcript)
- [ ] Signed in as `nagasivakumari26@gmail.com`, Omi **linked** in Vault & Engine → Connect your Omi
- [ ] **Clean slate:** strike every deed (Strike from the record) so the ledger starts empty
- [ ] Omi app open, phone mic ready

Fallback for a failed take: use the app's **"+ Witness a promise" → Type** scenario instead of Omi — it hits the same `/ingest → Lyzr → Qdrant` path.

---

## Scene 1 — Title card (0:00–0:05, 5s)
**SCREEN:** black card, on-screen text:
> **Smritaya — the witness for the verbal economy**
> Stop Prompting, Solo Agents · AI House × HiDevs

**SPEAK:** *"Smritaya is a witness for the verbal economy — it hears a promise once, remembers it forever, and defends it when the date passes."*

## Scene 2 — Landing (0:05–0:20, 15s)
**SCREEN:** landing hero "A billion people run on spoken promises…" → click **Launch App.**

**SPEAK:** *"Most of India runs on spoken promises — no paper, no proof. Smritaya keeps the memory and, when needed, the proof."*

## Scene 3 — Signed-in shell (0:20–0:30, 10s)
**SCREEN:** sidebar: **All Deeds · Witness Stand · Chambers · Vault & Engine.**

**SPEAK:** *"This is the Ledger — every promise I speak aloud lands here as a deed, with who, what, how much, and by when."*

## Scene 4 — The live Omi moment ⭐ (0:30–0:55, 25s)
**SCREEN:** ledger (empty) visible, your *Omi phone app* held into frame.
**ACTION:** start an Omi recording, speak clearly:

> *"Ramesh Yadav, wardrobe by Sunday, eight thousand."*

**ACTION:** stop the Omi recording → wait **~10s** → **hard refresh** the Ledger (Ctrl+Shift+R).

**SCREEN:** ONE deed appears:
> **Ramesh Yadav** — "wardrobe by Sunday" — **₹8,000** — **due 18 Oct**

**SPEAK:** *"One sentence, spoken once. Smritaya received Omi's webhook, Lyzr extracted the promise, and it's stored privately in Qdrant — one clean deed. Ten seconds after my voice stops. No typing."*

## Scene 5 — Second deed, second person (0:55–1:05, 10s)
**ACTION (optional):** repeat with another person for a fuller ledger:
> *"Sharmaji, repay my two thousand rupees by Friday."*
Refresh → a second deed appears.

**SPEAK:** *"Every person gets their own record. Smritaya separates the counterparties automatically."*

## Scene 6 — Recall / Ask (1:05–1:25, 20s)
**SCREEN:** Witness Stand (top of Ledger) or **Ask box**.
**ACTION:** type: *"What did Ramesh promise, and when is it due?"*

**SCREEN:** answer citing the deed: Ramesh Yadav — wardrobe — due Sun 18 Oct — ₹8,000.

**SPEAK:** *"Ask anything in plain language. Smritaya searches my private memory in Qdrant and answers with the actual record."*

## Scene 7 — The Hearing ⭐ (1:25–1:50, 25s)
**SCREEN:** click the **Ramesh Yadav** deed → **Hearing / Recommend.**
Pan top→bottom: **Summons** (verbatim words, dated) → **Evidence** ("Ramesh Yadav wardrobe Sunday", due 18 Oct, status pending) → **Pattern** (seal) → The Memo (gentle / firm / formal).

**ACTION:** tap **copy** on the gentle note, show it pasted.

**SPEAK:** *"When the date passes quietly, Smritaya convenes a hearing: the exact words, the pattern of the person's word, and three ready-to-send messages — gentle first, firm second, formal notice last. Every tool of a witness who never forgets."*

## Scene 8 — Nudge to Omi (1:50–2:05, 15s) — optional
**SCREEN:** **Remind** button on the deed.

**SPEAK:** *"And the reminder reaches the person's Omi — the same channel the promise came through."*

*(If notifications aren't live in your build, say: "notifications go straight to your Omi app.")*

## Scene 9 — Privacy: Strike from the record ⭐ (2:05–2:15, 10s)
**SCREEN:** open one deed → **Strike from the record** → deed gone; ledger refreshed.

**SPEAK:** *"Privacy is a legal right here, not a setting. One tap — the witness forgets on command. That's the privacy-first promise: your words, your memory, your deletion."*

## Scene 10 — Closing (2:15–2:30, 15s)
**SCREEN:** black card:
> **Speak once. Remembered forever. Defended when you need it.**
> Smritaya · Omi → Lyzr → Qdrant → FastAPI → React
> github.com/NagasivaKumari/Smritaya

**SPEAK:** *"Smritaya — speak once, remembered forever, defended when you need it. Thank you."*

---

## Filming tips
- Record **Scenes 4** first (live demo is the risky one), then film the rest in recognition order.
- If Omi lags, keep the stock by using manual "*Witness a promise* → type" — same backend, same storage.
- Real camera or a screen recorder with your voice — either is fine. Keep it one take per scene so editing is a simple join.
- Total runtime ~2.5 minutes. Under 3 minutes is the cap.

**Omi integration (for the judges' Q&A):** every Omi call hits `POST /omi/conversation` / `POST /omi/realtime` (FastAPI), the payload is parsed for any shape, the deed maps to the *linked* account via its Omi uid, extraction runs on **Lyzr**, vectors + full text live in **Qdrant** (local mode = your data never leaves your machine), and reminders go back to Omi's notification API.