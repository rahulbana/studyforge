# StudyForge

A unified web app that turns a chapter PDF into **topper-grade study notes** and a
**verified question bank**, powered by an OpenAI agent that also researches the topic
online while writing the notes.

Upload a chapter PDF → tell it the class, subject and chapter name → the agent:

1. Reads the PDF and researches how the same topic is taught elsewhere (schools,
   universities, coaching centres) using OpenAI's web-search tool.
2. Writes **exhaustive, exam-prep notes** aimed at elite / topper students — every
   concept covered, multiple worked examples, solved problems, formula sheets, common
   misconceptions, plus **visuals**: **Mermaid charts** (flowcharts, cycles,
   comparisons) and **detailed, labelled SVG figures**. A dedicated diagram pass
   renders each figure separately so illustrations are detailed rather than rough
   sketches (`ENABLE_DIAGRAMS` / `MAX_DIAGRAMS` in `.env`).
3. Generates questions of every type you ask for — **True/False, MCQ, Fill in the
   blanks, One-word, Short, Long, Case-based** — each with a model answer.
4. **Verifies** every answer and auto-fixes the ones that are wrong (flagging any it
   can't confirm for review).
5. Keeps everything (uploaded + generated Q/A) in a local database and lets you
   **export** notes and questions to **PDF** or **Word (DOCX)** — including a
   **worksheet** layout (questions only, then a separate **answer key**) for paper practice.

## Two modes: Study & Evaluate

Toggle in the header:

- **Study** — the flow above: upload a chapter, get notes, a question bank, and sources.
- **Evaluate** — test yourself and get graded. Pick an uploaded chapter *or* type a
  class/subject/topic, choose your question mix, and the agent generates a test. You
  answer and submit; the agent **grades every answer** (objective answers exactly,
  written answers with partial credit), computes an overall **score**, and produces a
  **per-concept weak-area breakdown** plus a study report telling you exactly where to
  spend more time. Attempts are saved, and a **Progress** view charts your score over
  time and surfaces the concepts you repeatedly score low on across tests.

## Tech stack

| Layer      | Choice                                            |
|------------|---------------------------------------------------|
| Backend    | Python 3.12 · FastAPI · SQLAlchemy · SQLite       |
| LLM        | OpenAI (`gpt-4o` by default) + `web_search` tool  |
| PDF        | pypdf (text extraction)                           |
| Export     | reportlab (PDF) · python-docx (Word)              |
| Frontend   | React (Vite) · Chakra UI · react-markdown         |

## Prerequisites

- An **OpenAI API key** (required)
- Either **Docker** (easiest — see below), or **Python 3.12** + **Node.js 18+/npm** for local dev

## Run with Docker (one command)

The quickest way — no Python/Node setup, just Docker:

```bash
cp backend/.env.example backend/.env     # then add your OPENAI_API_KEY
docker compose up --build
```

Open **http://localhost:8080** (the API/docs are also exposed at
http://localhost:8000/docs). The backend runs migrations automatically on start,
the SQLite database persists in `backend/data/`, and nginx serves the built
frontend and proxies `/api` (including live-notes streaming) to the backend.

## Deploy to Google Cloud Run

A one-command deploy (two services, ephemeral-SQLite demo) with a secret-managed
OpenAI key lives in [`deploy/cloudrun/`](deploy/cloudrun/README.md):

```bash
export PROJECT_ID=your-gcp-project
export OPENAI_API_KEY=sk-...
./deploy/cloudrun/deploy.sh
```

See that guide for durable data (Cloud SQL) and hardening.

## Quick start (without Docker)

```bash
# 1. Install everything from scratch.
#    NOTE: setup.sh is a CLEAN install — it removes any existing backend/.venv,
#    frontend/node_modules and backend/.env, then recreates everything. A real
#    OPENAI_API_KEY already in backend/.env is preserved and restored.
./setup.sh

# 2. Add your key (only needed the first time; later runs preserve it)
#    edit backend/.env  ->  OPENAI_API_KEY=sk-...

# 3. Run backend + frontend together
./start.sh
```

Then open **http://localhost:5173**. The API docs live at
**http://localhost:8000/docs**.

## Configuration (`backend/.env`)

| Variable            | Default                              | Purpose                                        |
|---------------------|--------------------------------------|------------------------------------------------|
| `OPENAI_API_KEY`    | —                                    | Required.                                      |
| `OPENAI_MODEL`      | `gpt-4o`                             | Model for notes/questions/verification.        |
| `ENABLE_WEB_SEARCH` | `true`                               | Let the notes agent browse the web.            |
| `DEEP_SEARCH`       | `false`                              | More thorough web research (deeper, slower).   |
| `ENABLE_DIAGRAMS`   | `true`                               | Render detailed SVG figures (1 call each).     |
| `MAX_DIAGRAMS`      | `8`                                  | Max figures rendered per chapter.              |
| `BATCH_VERIFICATION`| `true`                               | Verify all answers in one call (fewer 429s).   |
| `STREAM_NOTES`      | `true`                               | Stream notes live (SSE) instead of a spinner.  |
| `PRICE_INPUT_PER_1M`| `2.5`                                | USD per 1M input tokens (for cost estimate).   |
| `PRICE_OUTPUT_PER_1M`| `10.0`                              | USD per 1M output tokens (for cost estimate).  |
| `MAX_UPLOAD_MB`     | `25`                                 | Reject uploaded PDFs larger than this.         |
| `ENABLE_OCR`        | `true`                               | OCR scanned/image PDFs (needs Tesseract).      |
| `OCR_DPI`           | `200`                                | Render resolution for OCR.                     |
| `OCR_MAX_PAGES`     | `50`                                 | Max pages to OCR per scanned PDF.              |
| `LOG_FORMAT`        | `text`                               | `text` (readable) or `json` (structured logs). |
| `METRICS_ENABLED`   | `true`                               | Expose Prometheus metrics at `GET /metrics`.   |
| `DATABASE_URL`      | `sqlite:///./data/study_notes.db`    | SQLite (default) or a `postgresql+psycopg://…` URL — see below. |
| `CORS_ORIGINS`      | `http://localhost:5173,...`          | Allowed frontend origins.                      |

### Database (SQLite or Postgres)

The backend is database-agnostic (SQLAlchemy + Alembic) — switch entirely via
`DATABASE_URL` in `backend/.env`; migrations run automatically on startup either way.

- **SQLite** (default): `sqlite:///./data/study_notes.db` — zero setup, single file.
- **Postgres** (durable / multi-instance): `postgresql+psycopg://USER:PASS@HOST:5432/DB`.

For a local Postgres with Docker, a `postgres` profile is included:

```bash
# set DATABASE_URL in backend/.env to:
#   postgresql+psycopg://studyforge:studyforge@postgres:5432/studyforge
docker compose --profile postgres up --build
```

The backend waits for Postgres to be ready before migrating, and **creates the
database if it doesn't exist yet** (needs a user with CREATEDB; otherwise it
prints a clear error telling you to create it). Plain `docker compose up` uses
SQLite (the postgres service is gated behind the profile).

### Observability

- **Logs** carry a correlation id (`request_id`) tying each request or background
  job (`notes:{id}`, `questions-job:{id}`, …) to all of its log lines. Set
  `LOG_FORMAT=json` for structured, shipper-friendly output.
- **Metrics**: `GET /metrics` (on the backend, `:8000`) serves Prometheus text —
  LLM call latency/retries/429s/tokens/cost, web-search usage, HTTP request rates,
  and live gauges for chapters/jobs/assessments by status and total spend.
- **Dashboards** (optional): a Prometheus + Grafana stack is wired to `/metrics`
  behind a Compose profile — turns the metrics above into charts:

  ```bash
  docker compose --profile monitoring up --build
  ```

  Grafana at http://localhost:3000 (anonymous access) opens with the pre-provisioned
  **StudyForge** dashboard; Prometheus is at http://localhost:9090. Plain
  `docker compose up` (no profile) runs just the app. Config lives in `monitoring/`.

## Architecture

📐 **Diagrams:** see [`docs/architecture.md`](docs/architecture.md) — system overview,
request layering, the notes/questions/assessment flows, startup/migrations, and
deployment (rendered on GitHub).

The backend follows a clean, layered design (request → route → service →
repository/agent → model), so HTTP concerns, business logic, data access and
LLM calls stay decoupled and independently testable.

```
HTTP ─▶ api/routes ─▶ services ─▶ repositories ─▶ models (SQLAlchemy)
                          │
                          └─▶ agents ─▶ agents/llm (OpenAI client, retries)
                                   └─▶ agents/prompts (all prompt templates)

 core/    config · logging · exceptions (+ handlers)
 schemas/ pydantic request/response models
 utils/   pdf extraction · markdown helpers
```

- **Routes** are thin: validate input, call a service, return a schema.
- **Services** own orchestration (upload → notes → diagrams, generate → verify).
- **Repositories** isolate all DB access behind small functions.
- **Agents** are focused (`notes`, `question`, `verifier`, `diagram`) and share
  one retrying `LLMClient`; every prompt lives in `agents/prompts.py`.
- **Errors** raise domain exceptions (`NotFoundError`, `ValidationError`,
  `AgentError`) that a single handler maps to clean HTTP responses.
- **Notes** are generated in the background right after upload; the UI polls until
  they're ready, so a slow web-search run never blocks the page.
- **Question generation** also runs in the background as a tracked job: the
  `generate` endpoint returns a job immediately (`202`), the work happens in a
  background task, and the UI polls `GET /api/generation-jobs/{id}` and shows a
  toast when it's done. You can keep working (even switch tabs) while it runs.
- **Verification** statuses: `verified` (correct), `corrected` (auto-fixed),
  `needs_review` (couldn't confirm from the material), `unverified` (not yet checked).
- Editing a question resets it to `unverified`.
- **Dark mode**: toggle in the header (defaults to your OS setting); diagrams stay on
  a light surface so generated figures remain legible in either theme.
- **Live notes**: with `STREAM_NOTES=true`, notes stream into the page token-by-token
  over Server-Sent Events (generation runs in a background thread, so it finishes
  even if you navigate away); diagrams render once writing completes.
- **Cost tracking**: token usage for notes, diagrams, questions and tests is recorded
  and shown as an estimated USD cost (per-chapter badge, per-test on results), priced
  by `PRICE_INPUT_PER_1M` / `PRICE_OUTPUT_PER_1M`.
- **Sources**: the web pages the notes agent cited during research are captured
  from the OpenAI web-search result and shown in a **Sources** tab (and stored on
  the chapter). Empty when web search was disabled or unavailable.

## Project layout

```
.                                    # repo root
├── setup.sh · start.sh · Makefile · docker-compose.yml
├── deploy/cloudrun/ · monitoring/       # Cloud Run deploy + Prometheus/Grafana
├── backend/
│   ├── Dockerfile · pyproject.toml · requirements.txt · .env.example
│   ├── alembic.ini · alembic/            # database migrations (Alembic)
│   ├── app/
│   │   ├── main.py               # app factory (create_app)
│   │   ├── core/                 # config, logging, exceptions
│   │   ├── db/                   # engine, session, Base
│   │   ├── models/               # Chapter, Question, enums
│   │   ├── schemas/              # pydantic (chapter, question, common)
│   │   ├── repositories/         # data access (chapter_repo, question_repo)
│   │   ├── services/             # chapter / question / export orchestration
│   │   ├── agents/               # llm client, prompts, notes/question/verifier/diagram
│   │   ├── api/routes/           # chapters, questions, export, meta
│   │   └── utils/                # pdf, markdown
│   └── tests/                    # pytest (api, export, diagram agent)
└── frontend/
    ├── Dockerfile · nginx.conf
    └── src/
        ├── App.jsx · main.jsx · theme.js · constants.js
        ├── lib/                  # axios client, download helper
        ├── api/                  # chapters, questions, meta
        ├── hooks/                # useHealth, useChapters, useChapterWorkspace
        ├── components/common/    # Markdown, Mermaid
        ├── components/layout/    # Header, Sidebar
        └── features/             # chapters/*, questions/*
```

## Development

```bash
make test      # backend pytest suite
make test-web  # frontend Vitest suite (hooks, SSE, render smoke)
make lint      # ruff check
make fmt       # ruff --fix
```

Backend tests never hit OpenAI — they stub the `LLMClient`. Frontend tests
(Vitest + React Testing Library, jsdom) mock the API modules and `EventSource`,
so they run fully offline.

### Database migrations (Alembic)

The schema is managed with Alembic. On startup the app brings the database to the
latest revision automatically (fresh DBs are created; pre-Alembic DBs are adopted
by stamping the baseline), so there's nothing to run by hand for normal use.

When you change a model, generate and apply a migration:

```bash
make revision m="add my column"   # autogenerate from model changes
make migrate                      # apply (alembic upgrade head)
```

Migration files live in `backend/alembic/versions/`.

## Notes on cost / scanned PDFs

- Each generation/verification call uses the OpenAI API, so counts are capped at 25
  per type and notes context is trimmed to a sane length.
- The PDF must contain selectable text. Scanned (image-only) PDFs won't extract; run
  them through OCR first.
