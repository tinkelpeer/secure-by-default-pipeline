#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:?Usage: ./scripts/verify-image.sh <image-ref> <owner/repo> [workflow-path] [branch] }"
REPO="${2:?Usage: ./scripts/verify-image.sh <image-ref> <owner/repo> [workflow-path] [branch] }"
WORKFLOW_PATH="${3:-.github/workflows/ci.yml}"
BRANCH="${4:-main}"

EXPECTED_IDENTITY="https://github.com/${REPO}/${WORKFLOW_PATH}@refs/heads/${BRANCH}"
EXPECTED_ISSUER="https://token.actions.githubusercontent.com"

echo "==> Verifying Cosign signature"
echo "Expected identity: ${EXPECTED_IDENTITY}"
echo "Expected issuer:   ${EXPECTED_ISSUER}"

cosign verify \
  --certificate-identity "${EXPECTED_IDENTITY}" \
  --certificate-oidc-issuer "${EXPECTED_ISSUER}" \
  "${IMAGE_REF}" >/dev/null

echo "==> Signature verification passed"

echo "==> Verifying GitHub provenance attestation"
gh attestation verify \
  "oci://${IMAGE_REF}" \
  --repo "${REPO}" \
  --signer-workflow "${REPO}/${WORKFLOW_PATH}" >/dev/null

echo "==> Provenance attestation verification passed"

echo "==> POLICY RESULT: ALLOW"
echo "Image ${IMAGE_REF} satisfies the verification rule."