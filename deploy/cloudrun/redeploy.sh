#!/usr/bin/env bash
#
# Rebuild and redeploy both Cloud Run services (backend + frontend), reusing the
# infra that deploy.sh created (APIs, Artifact Registry repo, secret). Use this
# for routine updates after the first ./deploy.sh.
#
# Usage:
#   export PROJECT_ID=my-gcp-project
#   ./deploy/cloudrun/redeploy.sh
#
# Optional:
#   OPENAI_API_KEY=sk-...   also rotates the secret (adds a new version)
#   BACKEND_ONLY=1          rebuild + redeploy only the backend
#   FRONTEND_ONLY=1         rebuild + redeploy only the frontend
#   REGION, REPO, BACKEND_SERVICE, FRONTEND_SERVICE, SECRET_NAME  override defaults
set -euo pipefail

# --- Config (must match deploy.sh) ---------------------------------------
PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your GCP project id}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-studyforge}"
BACKEND_SERVICE="${BACKEND_SERVICE:-studyforge-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-studyforge-frontend}"
SECRET_NAME="${SECRET_NAME:-studyforge-openai-key}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AR_HOST="${REGION}-docker.pkg.dev"
BACKEND_IMAGE="${AR_HOST}/${PROJECT_ID}/${REPO}/backend:latest"
FRONTEND_IMAGE="${AR_HOST}/${PROJECT_ID}/${REPO}/frontend:latest"

DO_BACKEND=1; DO_FRONTEND=1
[ "${BACKEND_ONLY:-0}" = "1" ] && DO_FRONTEND=0
[ "${FRONTEND_ONLY:-0}" = "1" ] && DO_BACKEND=0

echo "==> Redeploy to project ${PROJECT_ID} / region ${REGION}"
gcloud config set project "${PROJECT_ID}" >/dev/null

# Sanity: infra from the first deploy must exist.
if ! gcloud artifacts repositories describe "${REPO}" --location "${REGION}" >/dev/null 2>&1; then
  echo "ERROR: Artifact Registry repo '${REPO}' not found. Run ./deploy/cloudrun/deploy.sh first." >&2
  exit 1
fi

# Optional key rotation.
if [ -n "${OPENAI_API_KEY:-}" ]; then
  echo "==> Rotating secret ${SECRET_NAME} (new version)"
  printf '%s' "${OPENAI_API_KEY}" | gcloud secrets versions add "${SECRET_NAME}" --data-file=-
fi

# --- Backend --------------------------------------------------------------
if [ "${DO_BACKEND}" = "1" ]; then
  echo "==> Building backend image"
  gcloud builds submit "${ROOT}/backend" --tag "${BACKEND_IMAGE}"

  echo "==> Redeploying backend"
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
fi

BACKEND_URL="$(gcloud run services describe "${BACKEND_SERVICE}" --region "${REGION}" --format='value(status.url)' 2>/dev/null || true)"
if [ -z "${BACKEND_URL}" ]; then
  echo "ERROR: backend service '${BACKEND_SERVICE}' not found. Run deploy.sh first." >&2
  exit 1
fi
BACKEND_HOST="${BACKEND_URL#https://}"
echo "==> Backend URL: ${BACKEND_URL}"

# --- Frontend -------------------------------------------------------------
if [ "${DO_FRONTEND}" = "1" ]; then
  echo "==> Building frontend image"
  gcloud builds submit "${ROOT}/frontend" \
    --config "${ROOT}/deploy/cloudrun/cloudbuild.frontend.yaml" \
    --substitutions "_IMAGE=${FRONTEND_IMAGE}"

  echo "==> Redeploying frontend (proxies /api -> ${BACKEND_HOST})"
  gcloud run deploy "${FRONTEND_SERVICE}" \
    --image "${FRONTEND_IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 --max-instances 3 \
    --cpu 1 --memory 256Mi \
    --timeout 3600 \
    --set-env-vars "BACKEND_HOST=${BACKEND_HOST}"
fi

FRONTEND_URL="$(gcloud run services describe "${FRONTEND_SERVICE}" --region "${REGION}" --format='value(status.url)' 2>/dev/null || true)"
echo ""
echo "==> Redeploy complete."
[ -n "${FRONTEND_URL}" ] && echo "    App:     ${FRONTEND_URL}"
echo "    Backend: ${BACKEND_URL}"
