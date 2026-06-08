#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:?Usage: ./scripts/show-attestation-claims.sh <image-ref> <owner/repo> [workflow-path] [branch] [predicate-type]}"
REPO="${2:?Usage: ./scripts/show-attestation-claims.sh <image-ref> <owner/repo> [workflow-path] [branch] [predicate-type]}"
WORKFLOW_PATH="${3:-.github/workflows/secure-release.yml}"
BRANCH="${4:-main}"
PREDICATE_TYPE="${5:-https://slsa.dev/provenance/v1}"

for bin in gh jq; do
  if ! command -v "${bin}" >/dev/null 2>&1; then
    echo "Error: required command not found: ${bin}" >&2
    exit 1
  fi
done

gh attestation verify \
  "oci://${IMAGE_REF}" \
  --repo "${REPO}" \
  --signer-workflow "${REPO}/${WORKFLOW_PATH}" \
  --source-ref "refs/heads/${BRANCH}" \
  --predicate-type "${PREDICATE_TYPE}" \
  --format json | jq '.[] | {
    predicateType: .verificationResult.statement.predicateType,
    subjects: .verificationResult.statement.subject,
    issuer: .verificationResult.signature.certificate.issuer,
    subject: .verificationResult.signature.certificate.subject,
    verifiedTimestamps: .verificationResult.verifiedTimestamps
  }'
