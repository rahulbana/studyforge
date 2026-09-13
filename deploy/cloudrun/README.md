# Deploy to Google Cloud Run

Deploys the app as **two Cloud Run services** — `studyforge-frontend` (nginx +
the built SPA) and `studyforge-backend` (FastAPI) — with the frontend proxying
`/api` to the backend, so the browser stays same-origin (no CORS).

> ⚠️ **Demo persistence.** This setup uses **ephemeral SQLite** (`/tmp` in the
> backend container). All chapters, questions and assessments **reset on every
> redeploy and every cold start**. For durable data, move to Cloud SQL — see
> [below](#making-data-durable-cloud-sql).

## Prerequisites

1. [`gcloud` CLI](https://cloud.google.com/sdk/docs/install), authenticated:
   ```bash
   gcloud auth login
   ```
2. A GCP project with **billing enabled**.
3. Your OpenAI API key.

## Deploy

From the repo root:

```bash
export PROJECT_ID=your-gcp-project-id
export OPENAI_API_KEY=sk-...        # only needed the first run (creates the secret)
./deploy/cloudrun/deploy.sh
```

The script is idempotent and does everything:

- enables the required APIs (Run, Cloud Build, Artifact Registry, Secret Manager);
- creates an Artifact Registry repo (`studyforge`);
- stores your key in **Secret Manager** (`studyforge-openai-key`) and grants the
  runtime service account access — the key is never baked into an image;
- builds + deploys the **backend** (CPU always on, 1 instance, so background
  generation runs and the ephemeral DB stays consistent);
- builds + deploys the **frontend**, wired to the backend's URL.

It prints the app URL at the end.

> 💰 **Cost note.** The backend runs one always-on instance with CPU always
> allocated (needed for background generation), so it bills continuously (~an
> always-up small instance) rather than scaling to zero. `LOG_FORMAT=json` sends
> structured logs to Cloud Logging.

Override defaults with env vars: `REGION` (default `us-central1`), `REPO`,
`BACKEND_SERVICE`, `FRONTEND_SERVICE`, `SECRET_NAME`.

## Updating

Rebuild + redeploy both services (reuses the existing APIs / repo / secret):

```bash
export PROJECT_ID=your-gcp-project
./deploy/cloudrun/redeploy.sh
```

Options: `BACKEND_ONLY=1` or `FRONTEND_ONLY=1` to redeploy just one; set
`OPENAI_API_KEY` to also rotate the secret. (Re-running `deploy.sh` works too;
`redeploy.sh` just skips the one-time setup.)

## Why these settings

- **Backend: `--no-cpu-throttling` + `--min-instances 1 --max-instances 1`.**
  Notes/question/assessment generation runs *after* the HTTP response (FastAPI
  `BackgroundTasks` / threads); Cloud Run would otherwise freeze the CPU once the
  response is sent. Pinning to one always-on instance also keeps the single
  SQLite writer consistent. `--timeout 3600` allows long SSE note streams.
- **Frontend: nginx template.** `listen $PORT` and the backend host are filled in
  at container start (`NGINX_ENVSUBST_FILTER`); `/api` is proxied over HTTPS with
  a `resolver` so the backend's `run.app` IP is re-resolved at request time.
- **OCR** works out of the box — the backend image installs Tesseract.

## Making data durable (Cloud SQL)

When you outgrow the demo:

1. Create a Cloud SQL for PostgreSQL instance + database.
2. The psycopg 3 driver is already in `backend/requirements.txt` — nothing to add.
3. Deploy the backend with the Cloud SQL connection and a Postgres URL, e.g.:
   ```bash
   gcloud run deploy studyforge-backend ... \
     --add-cloudsql-instances PROJECT:REGION:INSTANCE \
     --set-env-vars "DATABASE_URL=postgresql+psycopg://USER:PASS@/DBNAME?host=/cloudsql/PROJECT:REGION:INSTANCE"
   ```
   Alembic runs on startup and creates the schema. You can then drop
   `--min/max-instances 1` and let it scale.

## Hardening (optional)

- The backend is deployed `--allow-unauthenticated` for simplicity. To lock it to
  the frontend only, make it private (`--no-allow-unauthenticated`), give the
  frontend service account `roles/run.invoker` on it, and have nginx attach an
  identity token — or put both behind a load balancer / IAP.
- Add app-level auth (per-student accounts) before real multi-user use.

## Tear down

```bash
export PROJECT_ID=your-gcp-project
./deploy/cloudrun/clean.sh                 # delete the two Cloud Run services
DELETE_ALL=1 ./deploy/cloudrun/clean.sh    # also remove the AR repo + secret
FORCE=1 ./deploy/cloudrun/clean.sh         # skip the confirmation prompt
```
