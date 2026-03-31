#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:?Usage: ./scripts/deny-example.sh <image-ref> <owner/repo>}"
REPO="${2:?Usage: ./scripts/deny-example.sh <image-ref> <owner/repo>}"

echo "==> Running deny example"
echo "This intentionally checks the image against the WRONG workflow identity."
echo

if ./scripts/verify-image.sh "${IMAGE_REF}" "${REPO}" ".github/workflows/not-the-real-workflow.yml" "main"; then
  echo
  echo "UNEXPECTED RESULT: verification passed"
  echo "Your policy is too weak if this happens."
  exit 1
else
  echo
  echo "EXPECTED RESULT: DENY"
  echo "The image was rejected because the signer workflow identity did not match the approved workflow."
fi