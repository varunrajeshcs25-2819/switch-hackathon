# PatchPilot

**Multi-agent visual bug detection and investigation.**

A developer uploads a screenshot of a broken UI. Three specialised agents —
Vision → Triage → Investigation — collaborate through a persisted room,
produce an evidence-based root-cause report, and are explicit about what is
*visible*, what is *inferred*, and what is *verified*.

---

## 1. What actually runs

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + Tailwind CSS v4 + Lucide icons |
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Persistence | SQLite (`backend/patchpilot.db`, stdlib `sqlite3`) |
| Models | Google Gemini via `google-genai` (`gemini-2.0-flash` by default) |
| Agent collaboration | Switch-style room (`backend/integrations/switch/room.py`) |

### The honest Switch situation

The official Switch agent SDK is **not installed** in this environment and no
Switch endpoints/documentation are reachable from the sandbox. Rather than
invent undocumented protocol details, `backend/integrations/switch/room.py`
implements the same semantics locally:

- unique agent identities (`vision`, `triage`, `investigation`)
- explicit addressing (sender → recipient, plus room broadcasts)
- structured message kinds (`observation`, `classification`, `task`,
  `findings`, `challenge`, `verdict`, `error`)
- duplicate suppression (`dedupe_key`) and a hard message cap that prevents
  infinite agent ping-pong
- persisted transcript per issue, exposed at `GET /issues/{id}/messages`

`SwitchRoom._deliver()` is the only transport-specific method. To move to the
real Switch transport, publish the `AgentMessage` there; the message contract,
persistence, guards and REST surface stay unchanged.

**No agent conversation is scripted.** Every message is generated inside
`backend/services/workflow.py` from an agent's actual output, or from an actual
exception (an `error` message). Nothing in the UI fakes a transcript.

---

## 2. Architecture

```
frontend/src/pages/            Dashboard · New Analysis · Agent Collaboration · Reports
        │  fetch
        ▼
backend/api/main.py            REST API, SQLite load/save, stats
        │
        ▼
backend/services/workflow.py   runs the three agents, posts to the room,
        │                      computes challenges + triage verdict
        ├── agents/vision/                 agent.py + prompts.py
        ├── agents/triage/                 agent.py + prompts.py
        └── agents/investigation/          agent.py + prompts.py
        │
        ├── backend/integrations/switch/room.py    message contract + guards
        └── backend/database/                      store.py + serialization.py
```

### Response flow

1. `POST /issues/` validates the image (type, non-empty, ≤10 MB).
2. **Vision Agent** analyses the screenshot with Gemini (multimodal). It posts
   `observation` → `triage`.
3. **Triage Agent** classifies the issue and severity, broadcasts
   `classification`, then delegates with a `task` → `investigation`.
4. **Investigation Agent** inspects the supplied source code, posts `findings`
   → `triage`.
5. Deterministic, evidence-based checks in `workflow.py` add a `challenge`
   message when the outputs actually conflict (e.g. triage says backend error
   but no code evidence exists, or severity is critical while vision is
   uncertain).
6. Triage posts a `verdict` saying whether the investigation answered its
   objective, and what is still missing.
7. The issue, transcript and report are persisted to SQLite.

### Severity and honesty rules

- Severity follows the spec's Critical/High/Medium/Low definitions, driven by
  impact and evidence — not by how dramatic the screenshot looks.
- Without `GEMINI_API_KEY`, agents **do not invent results**: vision returns
  `confidence: uncertain` with an explicit note, triage uses transparent
  keyword rules, and investigation reports that no code-level conclusion is
  possible. Tests and the UI remain fully usable.
- The report separates observations, inferences and proposed fixes.

---

## 3. Setup

```bash
# 1. Backend
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 2. API key (free Google AI Studio key)
#    Windows: set GEMINI_API_KEY=...   macOS/Linux: export GEMINI_API_KEY=...
#    Or copy .env.example to .env (never commit .env)

# 3. Run the API from the patchpilot/ directory
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

```bash
# 4. Frontend (second terminal)
cd frontend
npm install
npm run dev            # http://127.0.0.1:5173
```

Set `VITE_API_BASE` if the API is not on `http://localhost:8000`.

### Tests

```bash
pip install pytest
python -m pytest tests -q
```

The suite exercises the room invariants, SQLite round-trip, all three agents
(fallback paths), the full workflow, message stream, source-code
re-investigation and stats — against the real app, with a temporary database.

---

## 4. API

| Method | Path | Purpose |
|---|---|---|
| POST | `/issues/` | Upload screenshot (+ optional `source_code`), run workflow |
| GET | `/issues/` | List issues |
| GET | `/issues/{id}` | Issue detail |
| GET | `/issues/{id}/messages` | Real agent transcript + per-agent counts |
| POST | `/issues/{id}/investigate` | Re-investigate with pasted source code |
| GET | `/stats` | Dashboard counters + recent activity |
| POST | `/agents/vision/analyze` | Vision Agent only |
| POST | `/agents/triage/classify` | Triage Agent only |
| POST | `/agents/investigate?issue_id=` | Investigation Agent only |
| GET | `/reports/{id}` | Final report |

Interactive docs: `http://127.0.0.1:8000/docs`.

---

## 5. Frontend screens

- **Dashboard** — live `/stats`: totals, open investigations, critical/high,
  awaiting attention, recent agent activity. Warns when no model key is set.
- **New Analysis** — screenshot upload + description + optional source code,
  then real Vision/Triage/Investigation results and a downloadable JSON report.
- **Agent Collaboration** — pick any issue and read its actual room transcript:
  sender → recipient, message kinds, timestamps, expandable payloads.
- **Investigation Reports** — live issue list and evidence-based report view.
This is the deployed app:
https://tobago-mentioned-disks-poetry.trycloudflare.com/

---

## 6. Security and reliability

- API keys only from environment variables; `.env` is git-ignored; the frontend
  never receives a key.
- Uploads validated by content type, non-empty body and 10 MB cap.
- The agents only see source code the developer explicitly pastes; there is no
  filesystem or repository access.
- No shell/command execution anywhere; agents cannot run code or push.
- Per-stage `asyncio.wait_for` timeout (`AGENT_TIMEOUT_SECONDS`, default 60 s);
  failures become `error` messages and are persisted, not hidden.
- Room guards: message cap, duplicate suppression, no self-addressing,
  participant allow-list.
- Activity logging carries agent role, action, success and error message.

---

## 7. Known limitations

1. **No official Switch SDK** in this environment — the room is a local
   implementation of the protocol semantics (see §1). It is explicitly labelled
   as such in code and UI copy.
2. **No automatic test execution** by the Investigation Agent: it may recommend
   tests, but never claims they passed. `actual_test_results` stays null unless
   a real runner is wired in.
3. **No screenshots persisted to disk** — the MVP stores a reference string and
   the agent's derived observations; add object storage for a full audit trail.
4. **SQLite document storage** (one JSON row per issue) — simple and adequate
   for an MVP; swap for normalised tables if queries grow.
5. Requires a Gemini API key for genuine model inference; without one the
   system runs in clearly-marked fallback mode.
