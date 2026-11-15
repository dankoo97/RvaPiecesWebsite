#!/usr/bin/env bash
# One-time setup that lets GitHub Actions (.github/workflows/deploy.yml) deploy to Cloud Run
# without a stored service-account key, using Workload Identity Federation.
# Safe to re-run: steps that already exist are skipped.
#
# Requires: gcloud (logged in as a project owner) and gh (logged in with admin on the repo).
set -euo pipefail

PROJECT_ID=rva-pieces-website
REPO=dankoo97/RvaPiecesWebsite
DEPLOY_SA_NAME=github-deployer
RUNTIME_SA=django-gcs-access@${PROJECT_ID}.iam.gserviceaccount.com
AR_LOCATION=us-central1
AR_REPO=rva-pieces-website-docker-repo
DB_BUCKET=rva-pieces-website_db
POOL=github
PROVIDER=github

# A newly created service account takes a little while to show up for IAM bindings.
retry() {
  for attempt in 1 2 3 4 5 6; do
    "$@" && return 0
    echo "  ...retrying in 10s (attempt $attempt)"
    sleep 10
  done
  return 1
}

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
DEPLOY_SA=${DEPLOY_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

echo "== Enabling APIs"
gcloud services enable iamcredentials.googleapis.com sts.googleapis.com --project "$PROJECT_ID"

echo "== Deploy service account"
gcloud iam service-accounts describe "$DEPLOY_SA" --project "$PROJECT_ID" >/dev/null 2>&1 ||
  gcloud iam service-accounts create "$DEPLOY_SA_NAME" --project "$PROJECT_ID" \
    --display-name "GitHub Actions deployer"

echo "== Granting deploy permissions"
# Deploy revisions and move traffic
retry gcloud projects add-iam-policy-binding "$PROJECT_ID" --condition=None --quiet \
  --member "serviceAccount:$DEPLOY_SA" --role roles/run.admin >/dev/null
# Push images
retry gcloud artifacts repositories add-iam-policy-binding "$AR_REPO" --project "$PROJECT_ID" \
  --location "$AR_LOCATION" --member "serviceAccount:$DEPLOY_SA" \
  --role roles/artifactregistry.writer >/dev/null
# Copy the prod database to the dev path
retry gcloud storage buckets add-iam-policy-binding "gs://$DB_BUCKET" \
  --member "serviceAccount:$DEPLOY_SA" --role roles/storage.objectUser >/dev/null
# Deploy revisions that run as the site's runtime service account
retry gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" --project "$PROJECT_ID" \
  --member "serviceAccount:$DEPLOY_SA" --role roles/iam.serviceAccountUser >/dev/null

echo "== Workload identity pool + GitHub provider"
gcloud iam workload-identity-pools describe "$POOL" --project "$PROJECT_ID" --location global >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools create "$POOL" --project "$PROJECT_ID" --location global \
    --display-name "GitHub Actions"
gcloud iam workload-identity-pools providers describe "$PROVIDER" --project "$PROJECT_ID" \
  --location global --workload-identity-pool "$POOL" >/dev/null 2>&1 ||
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" --project "$PROJECT_ID" \
    --location global --workload-identity-pool "$POOL" \
    --display-name "GitHub" \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition "assertion.repository == '$REPO'"

echo "== Allowing $REPO workflows to act as the deploy service account"
retry gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" --project "$PROJECT_ID" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository/$REPO" >/dev/null

echo "== Saving GitHub repo variables"
gh variable set GCP_WIF_PROVIDER --repo "$REPO" \
  --body "projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"
gh variable set GCP_DEPLOY_SA --repo "$REPO" --body "$DEPLOY_SA"

echo "Done. Pushes to main/dev will now deploy."
