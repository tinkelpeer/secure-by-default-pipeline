#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${1:?Usage: ./scripts/collect-evidence.sh <image-ref> <owner/repo> [workflow-path] [branch]}"
REPO="${2:?Usage: ./scripts/collect-evidence.sh <image-ref> <owner/repo> [workflow-path] [branch]}"
WORKFLOW_PATH="${3:-.github/workflows/secure-release.yml}"
BRANCH="${4:-main}"
OUT_DIR="${OUT_DIR:-evidence}"

mkdir -p "${OUT_DIR}"
./scripts/verify-image.sh "${IMAGE_REF}" "${REPO}" "${WORKFLOW_PATH}" "${BRANCH}" | tee "${OUT_DIR}/verification.log"
./scripts/show-attestation-claims.sh "${IMAGE_REF}" "${REPO}" "${WORKFLOW_PATH}" "${BRANCH}" > "${OUT_DIR}/provenance-claims.json"
./scripts/show-attestation-claims.sh "${IMAGE_REF}" "${REPO}" "${WORKFLOW_PATH}" "${BRANCH}" "https://spdx.dev/Document/v2.3" > "${OUT_DIR}/sbom-claims.json" || true
cat > "${OUT_DIR}/README.md" <<REPORT
# Verification evidence

Image: \\`${IMAGE_REF}\\`
Repository: \\`${REPO}\\`
Workflow: \\`${WORKFLOW_PATH}\\`
Branch: \\`${BRANCH}\\`

Files:

- verification.log: allow/deny policy output
- provenance-claims.json: selected provenance attestation claims
- sbom-claims.json: selected SBOM attestation claims, if available
REPORT
printf 'Evidence written to %s\n' "${OUT_DIR}"
