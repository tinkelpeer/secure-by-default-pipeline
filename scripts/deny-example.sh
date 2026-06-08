#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:?Usage: ./scripts/deny-example.sh <image-ref> <owner/repo>}"
REPO="${2:?Usage: ./scripts/deny-example.sh <image-ref> <owner/repo>}"

printf '==> Running deny example\n'
printf 'This intentionally checks the image against the wrong workflow identity.\n\n'

if ./scripts/verify-image.sh "${IMAGE_REF}" "${REPO}" ".github/workflows/not-the-real-workflow.yml" "main"; then
  printf '\nUNEXPECTED RESULT: verification passed. The policy is too weak.\n'
  exit 1
else
  printf '\nEXPECTED RESULT: DENY. The image was rejected because the workflow identity did not match.\n'
fi
