#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/verify-image.sh <image-ref> <owner/repo> [workflow-path] [branch]

Example:
  ./scripts/verify-image.sh \
    ghcr.io/example/research-tool@sha256:0123abcd... \
    example/research-tool \
    .github/workflows/secure-release.yml \
    main
USAGE
}

IMAGE_REF="${1:-}"
REPO="${2:-}"
WORKFLOW_PATH="${3:-.github/workflows/secure-release.yml}"
BRANCH="${4:-main}"

if [[ -z "${IMAGE_REF}" || -z "${REPO}" ]]; then
  usage
  exit 1
fi

if [[ "${IMAGE_REF}" != *@sha256:* ]]; then
  cat >&2 <<'ERROR'
Error: image reference must use an immutable digest reference.

Use this form:
  ghcr.io/<owner>/<repo>@sha256:<digest>

Do not verify mutable tags such as:
  ghcr.io/<owner>/<repo>:latest
ERROR
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
PROVENANCE_PREDICATE="https://slsa.dev/provenance/v1"
SBOM_PREDICATES=("https://spdx.dev/Document/v2.3" "https://spdx.dev/Document")

printf '==> Policy inputs\n'
printf 'Image ref:           %s\n' "${IMAGE_REF}"
printf 'Expected identity:   %s\n' "${EXPECTED_IDENTITY}"
printf 'Expected issuer:     %s\n' "${EXPECTED_ISSUER}"
printf 'Expected workflow:   %s\n' "${EXPECTED_SIGNER_WORKFLOW}"
printf 'Expected source ref: %s\n\n' "${EXPECTED_SOURCE_REF}"

printf '==> Verifying Cosign keyless signature\n'
cosign verify \
  --certificate-identity "${EXPECTED_IDENTITY}" \
  --certificate-oidc-issuer "${EXPECTED_ISSUER}" \
  "${IMAGE_REF}" >/dev/null
printf 'PASS: image digest has a valid signature from the expected GitHub Actions identity.\n\n'

printf '==> Verifying SLSA provenance attestation\n'
gh attestation verify \
  "oci://${IMAGE_REF}" \
  --repo "${REPO}" \
  --signer-workflow "${EXPECTED_SIGNER_WORKFLOW}" \
  --source-ref "${EXPECTED_SOURCE_REF}" \
  --predicate-type "${PROVENANCE_PREDICATE}" >/dev/null
printf 'PASS: provenance attestation matches the expected repository, workflow, and ref.\n\n'

printf '==> Verifying SPDX SBOM attestation\n'
SBOM_OK=0
for predicate in "${SBOM_PREDICATES[@]}"; do
  if gh attestation verify \
      "oci://${IMAGE_REF}" \
      --repo "${REPO}" \
      --signer-workflow "${EXPECTED_SIGNER_WORKFLOW}" \
      --source-ref "${EXPECTED_SOURCE_REF}" \
      --predicate-type "${predicate}" >/dev/null 2>&1; then
    printf 'PASS: SBOM attestation found with predicate type %s.\n\n' "${predicate}"
    SBOM_OK=1
    break
  fi
done
if [[ "${SBOM_OK}" != 1 ]]; then
  echo "FAIL: no accepted SPDX SBOM attestation was found for this image." >&2
  exit 1
fi

printf '==> POLICY RESULT: ALLOW\n'
printf 'Image %s satisfies digest + signature + provenance + SBOM checks.\n' "${IMAGE_REF}"
