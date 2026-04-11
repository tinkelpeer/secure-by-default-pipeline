#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:?Usage: ./scripts/deny-example.sh <image-ref> <owner/repo>}"
REPO="${2:?Usage: ./scripts/deny-example.sh <image-ref> <owner/repo>}"

printf '==> Running deny example\n'
printf 'This intentionally checks the image against the WRONG workflow identity.\n\n'

if ./scripts/verify-image.sh "${IMAGE_REF}" "${REPO}" ".github/workflows/not-the-real-workflow.yml" "main"; then
  printf '\nUNEXPECTED RESULT: verification passed\n'
  printf 'Your policy is too weak if this happens.\n'
  exit 1
else
  printf '\nEXPECTED RESULT: DENY\n'
  printf 'The image was rejected because the signer workflow identity did not match the approved workflow.\n'
fi
