#!/usr/bin/env bash
#
# Deploy StudyForge to Google Cloud Run as TWO services
# (backend + frontend), with EPHEMERAL SQLite (demo — data resets on redeploy).
#
# Prereqs: gcloud CLI authenticated (`gcloud auth login`), billing enabled, and
# your OpenAI key available. Run from anywhere; paths are resolved relative to
# the repo.
#
# Usage:
#   export PROJECT_ID=my-gcp-project
#   export OPENAI_API_KEY=sk-...          # only needed the first time (creates the secret)
#   ./deploy/cloudrun/deploy.sh
#
# Override defaults via env: REGION, REPO, BACKEND_SERVICE, FRONTEND_SERVICE.
set -euo pipefail

# --- Config ---------------------------------------------------------------
PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your GCP project id}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-studyforge}"                       # Artifact Registry repo
BACKEND_SERVICE="${BACKEND_SERVICE:-studyforge-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-studyforge-frontend}"
SECRET_NAME="${SECRET_NAME:-studyforge-openai-key}"

# Repo root (this script lives in deploy/cloudrun/).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AR_HOST="${REGION}-docker.pkg.dev"
BACKEND_IMAGE="${AR_HOST}/${PROJECT_ID}/${REPO}/backend:latest"
FRONTEND_IMAGE="${AR_HOST}/${PROJECT_ID}/${REPO}/frontend:latest"

echo "==> Project ${PROJECT_ID} / region ${REGION}"
gcloud config set project "${PROJECT_ID}" >/dev/null

# --- Enable required APIs -------------------------------------------------
echo "==> Enabling APIs (run, cloudbuild, artifactregistry, secretmanager)"
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com >/dev/null

# --- Artifact Registry ----------------------------------------------------
if ! gcloud artifacts repositories describe "${REPO}" --location "${REGION}" >/dev/null 2>&1; then
  echo "==> Creating Artifact Registry repo '${REPO}'"
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker --location="${REGION}" \
    --description="StudyForge images"
fi

# --- OpenAI key secret ----------------------------------------------------
if ! gcloud secrets describe "${SECRET_NAME}" >/dev/null 2>&1; then
  if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: secret ${SECRET_NAME} doesn't exist and OPENAI_API_KEY is not set." >&2
    echo "       Set OPENAI_API_KEY and re-run to create it." >&2
    exit 1
  fi
  echo "==> Creating secret ${SECRET_NAME}"
  printf '%s' "${OPENAI_API_KEY}" | gcloud secrets create "${SECRET_NAME}" --data-file=-
elif [ -n "${OPENAI_API_KEY:-}" ]; then
  echo "==> Adding a new version to secret ${SECRET_NAME}"
  printf '%s' "${OPENAI_API_KEY}" | gcloud secrets versions add "${SECRET_NAME}" --data-file=-
fi

# Let Cloud Run's runtime service account read the secret.
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud secrets add-iam-policy-binding "${SECRET_NAME}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null 2>&1 || true

# --- Build + deploy BACKEND ----------------------------------------------
echo "==> Building backend image"
gcloud builds submit "${ROOT}/backend" --tag "${BACKEND_IMAGE}"

echo "==> Deploying backend service"
# CPU always allocated + min/max 1 instance: background jobs run after the HTTP
# response, and the ephemeral SQLite file stays consistent (one writer).
gcloud run deploy "${BACKEND_SERVICE}" \
  --image "${BACKEND_IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --no-cpu-throttling \
  --min-instances 1 --max-instances 1 \
  --cpu 1 --memory 1Gi \
  --timeout 3600 \
  --set-env-vars "DATABASE_URL=sqlite:////tmp/study_notes.db,STREAM_NOTES=true,LOG_FORMAT=json,LOG_FILE=/tmp/app.log" \
  --set-secrets "OPENAI_API_KEY=${SECRET_NAME}:latest"

BACKEND_URL="$(gcloud run services describe "${BACKEND_SERVICE}" --region "${REGION}" --format='value(status.url)')"
BACKEND_HOST="${BACKEND_URL#https://}"
echo "==> Backend URL: ${BACKEND_URL}"

# --- Build + deploy FRONTEND ---------------------------------------------
echo "==> Building frontend image"
gcloud builds submit "${ROOT}/frontend" \
  --config "${ROOT}/deploy/cloudrun/cloudbuild.frontend.yaml" \
  --substitutions "_IMAGE=${FRONTEND_IMAGE}"

echo "==> Deploying frontend service (proxies /api -> ${BACKEND_HOST})"
gcloud run deploy "${FRONTEND_SERVICE}" \
  --image "${FRONTEND_IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 --max-instances 3 \
  --cpu 1 --memory 256Mi \
  --timeout 3600 \
  --set-env-vars "BACKEND_HOST=${BACKEND_HOST}"

FRONTEND_URL="$(gcloud run services describe "${FRONTEND_SERVICE}" --region "${REGION}" --format='value(status.url)')"

echo ""
echo "============================================================"
echo " Deployed."
echo "   App:      ${FRONTEND_URL}"
echo "   Backend:  ${BACKEND_URL}   (docs at ${BACKEND_URL}/docs)"
echo ""
echo " NOTE: SQLite is EPHEMERAL — data resets on each redeploy/cold start."
echo "       For durable data, switch DATABASE_URL to Cloud SQL (Postgres)."
echo "============================================================"
