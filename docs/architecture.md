# StudyForge — Architecture

StudyForge turns a chapter PDF into topper-grade **notes**, a **verified question bank**,
and a self-**assessment** with per-concept feedback. It's a FastAPI backend + a
React/Vite/Chakra SPA, with a switchable SQLite/Postgres database and OpenAI for
generation (web-grounded).

> These diagrams are [Mermaid](https://mermaid.js.org/) and render automatically on GitHub.

## System overview

```mermaid
flowchart TB
  subgraph Client["Browser — React SPA (Vite + Chakra UI)"]
    UI["features/ (chapters, questions, assess)"]
    Hooks["hooks/ (data, polling, SSE state)"]
    APIc["lib/apiClient (axios)"]
    UI --> Hooks --> APIc
  end

  subgraph Edge["nginx (Docker / Cloud Run frontend)"]
    NGINX["serve built SPA<br/>reverse-proxy /api (+ SSE)"]
  end

  subgraph Backend["FastAPI backend — app/"]
    Routes["api/routes (thin controllers)"]
    Services["services (orchestration)"]
    Repos["repositories (DB access)"]
    Agents["agents (llm.py, prompts.py)"]
    Models["models (SQLAlchemy)"]
    Core["core (config, logging, metrics, exceptions)"]
    DBmod["db (session, migrate, doctor)"]
    Routes --> Services
    Services --> Repos
    Services --> Agents
    Repos --> Models
    Agents --> Models
    Routes -. errors/metrics .-> Core
    Services -. usage/logging .-> Core
  end

  subgraph Async["Async work (never blocks a request)"]
    BG["BackgroundTasks<br/>questions, assessments, notes"]
    SSE["NotesStream registry<br/>SSE streaming thread"]
  end

  DB[("Database<br/>SQLite (default) or Postgres")]
  OpenAI["OpenAI API<br/>chat + web_search tool"]

  subgraph Obs["Observability (optional profile)"]
    Metrics["GET /metrics (Prometheus text)"]
    Prom["Prometheus"]
    Graf["Grafana dashboard"]
    Metrics --> Prom --> Graf
  end

  APIc -->|HTTPS| NGINX
  NGINX -->|"/api/*"| Routes
  NGINX -->|"/api/chapters/:id/notes/stream"| SSE
  Services --> BG
  Services --> SSE
  BG --> Agents
  SSE --> Agents
  Agents -->|HTTPS| OpenAI
  Repos --> DB
  DBmod --> DB
  Core --> Metrics
```

## Request layering

Every request flows through one direction — no layer reaches back up:

```mermaid
flowchart LR
  R["api/routes<br/>validate + return schema"] --> S["services<br/>multi-step logic"]
  S --> RE["repositories<br/>get/list/add/save"]
  S --> AG["agents<br/>OpenAI calls"]
  RE --> M["models (ORM)"]
  AG --> M
```

## Flow 1 — Upload a chapter, stream notes (SSE)

```mermaid
sequenceDiagram
  actor U as Student
  participant FE as React SPA
  participant API as FastAPI
  participant ST as NotesStream
  participant AI as OpenAI
  participant DB as Database

  U->>FE: Upload PDF plus class/subject/chapter
  FE->>API: POST /api/chapters
  API->>API: validate PDF, OCR if scanned
  API->>DB: create Chapter, status pending
  API-->>FE: 200 ChapterDetail
  FE->>API: GET /api/chapters/:id/notes/stream
  API->>ST: start or attach stream thread
  ST->>AI: web-grounded notes, streamed
  AI-->>ST: token deltas
  ST-->>FE: SSE chunk events, live notes
  ST->>AI: diagram pass for SVG figures
  ST->>DB: save notes, sources, status ready
  ST-->>FE: SSE done
  FE->>API: GET /api/chapters/:id for final notes
```

## Flow 2 — Generate a question bank (background job + poll)

```mermaid
sequenceDiagram
  actor U as Student
  participant FE as React SPA
  participant API as FastAPI
  participant BG as BackgroundTask
  participant AI as OpenAI
  participant DB as Database

  U->>FE: Choose question types and counts
  FE->>API: POST /api/chapters/:id/questions/generate
  API->>DB: create GenerationJob, status pending
  API-->>FE: 202 with job_id
  API->>BG: schedule run_generation_job
  BG->>AI: generate per type
  BG->>AI: verify answers, batched
  BG->>DB: save questions, job done
  loop poll until settled
    FE->>API: GET /api/generation-jobs/:job_id
    API-->>FE: status
  end
  FE->>API: GET /api/chapters/:id/questions
```

## Flow 3 — Evaluate: generate a test, answer, grade

```mermaid
sequenceDiagram
  actor U as Student
  participant FE as React SPA
  participant API as FastAPI
  participant BG as BackgroundTask
  participant AI as OpenAI
  participant DB as Database

  U->>FE: Pick chapter or topic plus question mix
  FE->>API: POST /api/assessments
  API->>DB: create Assessment, status generating
  API-->>FE: 202 AssessmentDetail
  API->>BG: schedule run_generation
  BG->>AI: generate test questions
  BG->>DB: status ready
  FE->>API: poll GET /api/assessments/:id until ready
  U->>FE: Answer and submit
  FE->>API: POST /api/assessments/:id/submit
  API->>DB: status grading
  API->>BG: schedule run_grading
  BG->>AI: grade written answers, objective graded exactly
  BG->>DB: score plus per-concept feedback, status graded
  FE->>API: GET /api/assessments/progress
```

## Startup & migrations

```mermaid
flowchart TB
  Start["start.sh / container start"] --> Doctor["app.db.doctor (preflight)"]
  Doctor --> Ensure["ensure_database()<br/>wait for server; CREATE DATABASE if missing (Postgres)"]
  Ensure --> Mig["run_migrations() — Alembic"]
  Mig --> Fresh{"DB state?"}
  Fresh -->|fresh| Up["upgrade head (create schema)"]
  Fresh -->|"pre-Alembic (tables, no version)"| Stamp["stamp baseline, then upgrade"]
  Fresh -->|managed| Up2["upgrade head"]
  Up --> Verify["verify expected tables"]
  Stamp --> Verify
  Up2 --> Verify
  Verify --> Launch["launch uvicorn + SPA"]
```

## Deployment options

```mermaid
flowchart TB
  subgraph Local["Local dev — ./start.sh"]
    L1["uvicorn :8000"]
    L2["Vite dev :5173 (proxies /api)"]
  end

  subgraph Compose["Docker Compose"]
    C1["frontend nginx :8080"]
    C2["backend :8000"]
    C3[("postgres :5432<br/>profile: postgres")]
    C4["prometheus :9090 + grafana :3000<br/>profile: monitoring"]
    C1 --> C2
    C2 -.-> C3
    C4 -.-> C2
  end

  subgraph Cloud["Google Cloud Run (deploy/cloudrun)"]
    R1["studyforge-frontend (nginx)"]
    R2["studyforge-backend (FastAPI)"]
    R3["Secret Manager (OPENAI_API_KEY)"]
    R4[("Cloud SQL Postgres<br/>(optional, durable)")]
    R1 -->|"/api over HTTPS"| R2
    R2 --> R3
    R2 -.-> R4
  end
```

## Key cross-cutting pieces

| Concern | Where | Notes |
|---|---|---|
| Config / env flags | `core/config.py` | pydantic-settings; `DATABASE_URL`, `OPENAI_*`, `ENABLE_*`, `LOG_*`, `METRICS_ENABLED`, `MAX_UPLOAD_MB`, OCR, prices |
| LLM access | `agents/llm.py` | only place that calls the OpenAI SDK; retries, cost tracking, forced `web_search` |
| Prompts | `agents/prompts.py` | every prompt string lives here |
| Errors | `core/exceptions.py` | domain exceptions → one HTTP handler |
| Observability | `core/logging.py`, `core/metrics.py`, `api/routes/metrics.py` | JSON logs + correlation id; Prometheus metrics; DB gauges at scrape |
| Migrations | `db/migrate.py`, `alembic/` | auto-bootstrap; batch ALTER only on SQLite |
| DB switch | `db/session.py` | SQLite ↔ Postgres via `DATABASE_URL` |
