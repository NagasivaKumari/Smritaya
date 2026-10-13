# Smritaya

## The witness for the verbal economy

Smritaya is a privacy-first AI witness for spoken promises. It listens to
voice conversations through Omi, extracts commitments with Lyzr, stores the
original words and structured facts in Qdrant, and answers questions about
what was promised, by whom, and when.

It is designed for the everyday agreements that are often made without
paperwork: wages, loans, repairs, deliveries, rent, shop credit, and
informal business commitments.

> **Speak once. Remembered forever. Defended when you need it.**

## Hackathon submission

- **Hackathon:** Stop Prompting, Solo Agents â€” AI House Ã— HiDevs
- **Build track:** Privacy-First Knowledge Systems
- **Repository:** https://github.com/NagasivaKumari/Smritaya
- **Demo:** https://smritaya.vercel.app
- **Demo video:** `https://drive.google.com/file/d/1j4IRDWfzPgSSn8RygdNdob-AFDRqoibi/view?usp=sharing`
- **Entry:** Solo project

## What the product does

1. **Hear:** Omi sends a completed conversation or real-time transcript to
   Smritaya through a webhook.
2. **Extract:** The Lyzr Extractor identifies promises and returns structured
   deeds containing the counterparty, exact quote, direction, amount, due date,
   topic, and confidence.
3. **Remember:** The deed is embedded and stored in Qdrant with its verbatim
   words and structured metadata.
4. **Recall:** The user asks a natural-language question. Smritaya performs
   semantic retrieval together with user, person, status, and date filters.
5. **Testify:** The Lyzr Advisor answers only from the retrieved record and
   cites the stored deed.
6. **Defend:** For a broken promise, the Lyzr Drafter creates a Hearing memo
   with evidence and gentle, firm, and formal escalation messages.
7. **Close the loop:** Smritaya can draft and send a reminder to the userâ€™s
   Omi through the Omi notification API.

## Architecture

```text
 Omi voice / wearable
          |
          | conversation + real-time webhooks
          v
     FastAPI backend
          |
          +--> Lyzr Extractor --> structured deed
          |                           |
          |                           v
          |                    Qdrant testament
          |                    vector + metadata
          |                           |
          +<-- filtered semantic recall
          |
          +--> Lyzr Advisor  --> grounded answer
          |
          +--> Lyzr Drafter  --> Hearing memo
          |
          +--> Omi notification API --> reminder on phone

     React frontend: Ledger, Stand, Chambers, Hearing, Vault
```

The backend performs retrieval before calling Lyzr. This keeps the memory
layer under the applicationâ€™s control and allows Qdrant to run locally or
remotely.

## How the required technologies are used

### Omi

Omi is the ambient voice input and notification layer.

- `POST /omi/conversation` receives the completed conversation webhook.
- `POST /omi/realtime` receives real-time transcript batches.
- Omi UIDs can be linked to signed-in Smritaya accounts.
- Reminders can be sent back through the Omi notification API.

The webhook parser accepts the transcript shapes used by Omi conversation and
real-time events. Real-time fragments are buffered and deduplicated before
extraction.

### Qdrant

Qdrant is the persistent private memory layer. The `testament` collection
stores each deed as:

- A 384-dimensional semantic vector
- The exact spoken quote
- Counterparty and user ID
- Amount and currency
- Due timestamp
- Topic, direction, status, source, speaker, and reminders

Retrieval combines cosine similarity with payload filters. The default mode is
embedded Qdrant on disk, so no Qdrant account or separate server is required.
Remote Qdrant or Qdrant Cloud can be enabled with environment variables.

The Vault supports the privacy right to be forgotten: a user can delete one
deed or remove a counterpartyâ€™s records from the collection.

### Lyzr

Smritaya uses three specialized Lyzr Agent Studio agents:

- **Extractor:** transcript to structured deeds
- **Advisor:** retrieved deeds plus a question to a grounded answer
- **Drafter:** evidence to a four-part Hearing memo and escalation ladder

The backend creates a fresh Lyzr session for each operation so that one
transcript or question cannot leak into another request. If Lyzr is not
configured or temporarily unavailable, the application reports local mode and
uses its deterministic local reasoner so the product remains demoable.

## Privacy and trust controls

- Per-user retrieval isolation
- Omi identity linking
- Local Qdrant mode by default
- Exact quote retained as evidence
- Deed-level and counterparty-level deletion
- Explicit live/local status shown by the application
- No API keys stored in the repository

The local reasoner is a demo and resilience fallback. For production use,
configure the live Lyzr agents, protect the public webhook with
`SMRITAYA_OMI_SECRET`, and deploy Qdrant with appropriate access controls.

## Run locally

### Requirements

- Python 3.10 or newer
- Node.js and npm
- An Omi account/device for live voice testing
- Optional: Lyzr Agent Studio credentials
- Optional: ngrok or cloudflared for exposing webhooks to Omi

### 1. Start the backend

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

The backend loads a repository-root `.env` file automatically.

### 2. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally
`http://localhost:5173`.

For a production frontend build:

```powershell
npm run build
```

## Configuration

Copy `.env.example` to `.env` at the repository root.

### Lyzr

```dotenv
LYZR_API_KEY=your_key
LYZR_AGENT_ID=optional_shared_fallback_agent_id
LYZR_EXTRACTOR_AGENT_ID=optional_extractor_agent_id
LYZR_ADVISOR_AGENT_ID=optional_advisor_agent_id
LYZR_DRAFTER_AGENT_ID=optional_drafter_agent_id
LYZR_USER_ID=you@example.com
```

Separate agent IDs are recommended. If a specialized ID is not supplied,
Smritaya falls back to `LYZR_AGENT_ID`. If no Lyzr credentials are supplied,
the local reasoner is used.

### Qdrant

```dotenv
# Default: embedded, on-disk Qdrant
QDRANT_MODE=local
QDRANT_PATH=./qdrant_data

# Remote mode
# QDRANT_MODE=remote
# QDRANT_URL=http://localhost:6333
# QDRANT_API_KEY=
```

The first use creates the `testament` collection. FastEmbed uses
`BAAI/bge-small-en-v1.5` when available. If model loading fails, Smritaya uses
a deterministic local fallback embedding.

### Omi

```dotenv
OMI_APP_ID=your_omi_app_id
OMI_APP_SECRET=your_omi_app_secret
SMRITAYA_OMI_SECRET=optional_webhook_secret
```

For live Omi testing:

1. Start the backend.
2. Run `ngrok http 8000` or an equivalent HTTPS tunnel.
3. In Omi Developer Mode, set the conversation webhook to
   `https://YOUR_TUNNEL/omi/conversation`.
4. Set the real-time webhook to
   `https://YOUR_TUNNEL/omi/realtime`.
5. Speak a promise and wait for the deed to appear in the Ledger.

Example utterance:

> â€œRamesh Yadav, wardrobe by Sunday, eight thousand.â€

If Omi is not available, use **Witness a promise â†’ Type** in the frontend.
That path exercises the same extraction and Qdrant storage flow.

## API surface

| Endpoint | Purpose |
|---|---|
| `POST /omi/conversation` | Receive an Omi completed-conversation webhook |
| `POST /omi/realtime` | Receive Omi real-time transcript batches |
| `GET /health` | Report Qdrant, embedder, Lyzr, Omi, and point-count status |
| `GET /deeds` | Read the userâ€™s filterable Ledger |
| `POST /deeds` | Create a manual deed |
| `POST /ingest` | Ingest typed speech through the extraction flow |
| `POST /ask` | Ask a grounded question over recalled deeds |
| `POST /hearing` | Generate a Hearing memo for a deed |
| `POST /remind` | Draft and optionally send a reminder |
| `POST /status` | Mark a deed kept, broken, or contested |
| `POST /forget` | Delete deeds from the Qdrant record |
| `POST /auth/omi` | Link an Omi UID to a signed-in account |

## Demo flow

The complete recording plan is in [DEMO_SCRIPT.md](./DEMO_SCRIPT.md). A
recommended demonstration is:

1. Sign in and connect an Omi UID.
2. Speak a promise such as â€œRamesh Yadav, wardrobe by Sunday, eight thousand.â€
3. Show the deed appearing in the Ledger.
4. Ask, â€œWhat did Ramesh promise, and when is it due?â€
5. Open the deed and generate a Hearing memo.
6. Show the gentle, firm, and formal messages.
7. Use **Strike from the record** and show that the deed is deleted.

Keep the final video below the hackathonâ€™s five-minute limit and visibly show
voice input, retrieval, agent reasoning, and the resulting answer.

## Repository structure

```text
backend/
  app.py          FastAPI routes, auth, webhooks, orchestration
  agents.py       Lyzr agents and local reasoning fallback
  memory.py       Qdrant storage, embeddings, retrieval, deletion
  omi.py          Omi outbound notifications
  auth.py         Local account and session handling
  content.py      UI copy and seeded content
  test_*.py       Backend tests

frontend/
  src/
    App.jsx       Application shell and routing
    views/        Landing, Ledger, Stand, Chambers, Hearing, Vault
    components/  Reusable visual components
```

## Testing

```powershell
cd backend
python -m pytest

cd ..\frontend
npm run build
```

## Limitations and responsible use

Smritaya is a memory and communication aid, not a law firm or a guarantee
that a spoken agreement will be enforceable. Hearing messages are drafts and
should be reviewed before sending. Users should avoid recording people or
processing sensitive conversations without appropriate consent.

## License

No license file is currently included. Add the intended open-source license
before distributing the project outside the hackathon.
