#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:?Usage: ./scripts/show-attestation-claims.sh <image-ref> <owner/repo> [workflow-path] [branch] [predicate-type]}"
REPO="${2:?Usage: ./scripts/show-attestation-claims.sh <image-ref> <owner/repo> [workflow-path] [branch] [predicate-type]}"
WORKFLOW_PATH="${3:-.github/workflows/ci.yml}"
BRANCH="${4:-main}"
PREDICATE_TYPE="${5:-https://slsa.dev/provenance/v1}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: gh is required" >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required" >&2
  exit 1
fi

gh attestation verify \
  "oci://${IMAGE_REF}" \
  --repo "${REPO}" \
  --signer-workflow "${REPO}/${WORKFLOW_PATH}" \
  --source-ref "refs/heads/${BRANCH}" \
  --predicate-type "${PREDICATE_TYPE}" \
  --format json | jq '.[] | {
    predicateType: .verificationResult.statement.predicateType,
    subjects: .verificationResult.statement.subject,
    certificate: .verificationResult.signature.certificate,
    verifiedTimestamps: .verificationResult.verifiedTimestamps
  }'
