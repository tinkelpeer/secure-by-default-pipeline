#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./scripts/verify-image.sh <image-ref> <owner/repo> [workflow-path] [branch]

Example:
  ./scripts/verify-image.sh \
    ghcr.io/tinkelpeer/secure-by-default-pipeline@sha256:0123... \
    tinkelpeer/secure-by-default-pipeline \
    .github/workflows/ci.yml \
    main
EOF
}

IMAGE_REF="${1:-}"
REPO="${2:-}"
WORKFLOW_PATH="${3:-.github/workflows/ci.yml}"
BRANCH="${4:-main}"

if [[ -z "${IMAGE_REF}" || -z "${REPO}" ]]; then
  usage
  exit 1
fi

if [[ "${IMAGE_REF}" != *@sha256:* ]]; then
  cat >&2 <<EOF
Error: image reference must use an immutable digest reference.

Use this form:
  ghcr.io/<owner>/<repo>@sha256:<digest>

Not this form:
  ghcr.io/<owner>/<repo>:sha256-<digest>
EOF
  exit 1
fi

for bin in cosign gh; do
  if ! command -v "${bin}" >/dev/null 2>&1; then
    echo "Error: required command not found: ${bin}" >&2
    exit 1
  fi
done

EXPECTED_IDENTITY="https://github.com/${REPO}/${WORKFLOW_PATH}@refs/heads/${BRANCH}"
EXPECTED_ISSUER="https://token.actions.githubusercontent.com"
EXPECTED_SIGNER_WORKFLOW="${REPO}/${WORKFLOW_PATH}"
EXPECTED_SOURCE_REF="refs/heads/${BRANCH}"

printf '==> Policy inputs\n'
printf 'Image ref:           %s\n' "${IMAGE_REF}"
printf 'Expected identity:   %s\n' "${EXPECTED_IDENTITY}"
printf 'Expected issuer:     %s\n' "${EXPECTED_ISSUER}"
printf 'Expected workflow:   %s\n' "${EXPECTED_SIGNER_WORKFLOW}"
printf 'Expected source ref: %s\n\n' "${EXPECTED_SOURCE_REF}"

printf '==> Verifying Cosign signature\n'
cosign verify \
  --certificate-identity "${EXPECTED_IDENTITY}" \
  --certificate-oidc-issuer "${EXPECTED_ISSUER}" \
  "${IMAGE_REF}" >/dev/null
printf 'PASS: signature is present and bound to the expected GitHub Actions identity.\n\n'

printf '==> Verifying provenance attestation\n'
gh attestation verify \
  "oci://${IMAGE_REF}" \
  --repo "${REPO}" \
  --signer-workflow "${EXPECTED_SIGNER_WORKFLOW}" \
  --source-ref "${EXPECTED_SOURCE_REF}" >/dev/null
printf 'PASS: provenance attestation matches the expected repository, workflow, and ref.\n\n'

printf '==> Verifying SBOM attestation\n'
gh attestation verify \
  "oci://${IMAGE_REF}" \
  --repo "${REPO}" \
  --signer-workflow "${EXPECTED_SIGNER_WORKFLOW}" \
  --source-ref "${EXPECTED_SOURCE_REF}" \
  --predicate-type "https://spdx.dev/Document/v2.3" >/dev/null
printf 'PASS: SPDX SBOM attestation is present for this image.\n\n'

printf '==> POLICY RESULT: ALLOW\n'
printf 'Image %s satisfies signature + provenance + SBOM attestation checks.\n' "${IMAGE_REF}"
