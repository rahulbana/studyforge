#!/usr/bin/env bash
#
# Tear down the Cloud Run deployment. By default deletes only the two Cloud Run
# services. Set DELETE_ALL=1 to also remove the Artifact Registry repo (images)
# and the Secret Manager secret.
#
# Usage:
#   export PROJECT_ID=my-gcp-project
#   ./deploy/cloudrun/clean.sh              # delete the two services
#   DELETE_ALL=1 ./deploy/cloudrun/clean.sh # also delete AR repo + secret
#   FORCE=1 ./deploy/cloudrun/clean.sh      # skip the confirmation prompt
#
# Override defaults via env: REGION, REPO, BACKEND_SERVICE, FRONTEND_SERVICE,
# SECRET_NAME.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?Set PROJECT_ID to your GCP project id}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-studyforge}"
BACKEND_SERVICE="${BACKEND_SERVICE:-studyforge-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-studyforge-frontend}"
SECRET_NAME="${SECRET_NAME:-studyforge-openai-key}"
DELETE_ALL="${DELETE_ALL:-0}"

gcloud config set project "${PROJECT_ID}" >/dev/null

echo "About to delete from project '${PROJECT_ID}' (region ${REGION}):"
echo "  - Cloud Run service: ${FRONTEND_SERVICE}"
echo "  - Cloud Run service: ${BACKEND_SERVICE}"
if [ "${DELETE_ALL}" = "1" ]; then
  echo "  - Artifact Registry repo: ${REPO}  (all images)"
  echo "  - Secret Manager secret:  ${SECRET_NAME}"
fi

if [ "${FORCE:-0}" != "1" ]; then
  printf "Proceed? [y/N] "
  read -r reply
  case "${reply}" in
    y|Y|yes|YES) ;;
    *) echo "Aborted."; exit 0 ;;
  esac
fi

# --- Cloud Run services (delete regardless; ignore if already gone) --------
for svc in "${FRONTEND_SERVICE}" "${BACKEND_SERVICE}"; do
  if gcloud run services describe "${svc}" --region "${REGION}" >/dev/null 2>&1; then
    echo "==> Deleting Cloud Run service ${svc}"
    gcloud run services delete "${svc}" --region "${REGION}" --quiet
  else
    echo "    (service ${svc} not found — skipping)"
  fi
done

# --- Optional: images + secret -------------------------------------------
if [ "${DELETE_ALL}" = "1" ]; then
  if gcloud artifacts repositories describe "${REPO}" --location "${REGION}" >/dev/null 2>&1; then
    echo "==> Deleting Artifact Registry repo ${REPO}"
    gcloud artifacts repositories delete "${REPO}" --location "${REGION}" --quiet
  else
    echo "    (repo ${REPO} not found — skipping)"
  fi

  if gcloud secrets describe "${SECRET_NAME}" >/dev/null 2>&1; then
    echo "==> Deleting secret ${SECRET_NAME}"
    gcloud secrets delete "${SECRET_NAME}" --quiet
  else
    echo "    (secret ${SECRET_NAME} not found — skipping)"
  fi
fi

echo ""
echo "==> Cleanup complete."
[ "${DELETE_ALL}" != "1" ] && echo "    (kept the Artifact Registry repo + secret; DELETE_ALL=1 removes those too.)"
