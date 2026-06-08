# Secure-by-default pipeline check report

Generated: 2026-06-08T14:00:30.148932+00:00

Summary: **28 pass**, **1 warn**, **0 fail** out of 29 checks.

## Container

| Status | Check | Evidence | Fix |
|---|---|---|---|
| PASS | Dockerfile exists | Dockerfile found. | Keep it minimal and reproducible. |
| PASS | non-root container user | USER 65532:65532 | Run the application as a non-root user in the final image. |
| PASS | container healthcheck | HEALTHCHECK found. | Add a simple health check so deployment failures are visible. |
| WARN | base image digest pinning | FROM python:3.12-slim | For stronger reproducibility, pin the base image by digest after selecting the final base. |

## Dependencies

| Status | Check | Evidence | Fix |
|---|---|---|---|
| PASS | pinned Python dependencies | All direct requirements use == pins. | Pin direct dependencies with == and use Dependabot/dependency review for controlled updates. |
| PASS | dependency review workflow | dependency-review-action found. | Add a pull-request dependency review workflow. |
| PASS | Dependabot updates | Dependabot config found. | Enable Dependabot for GitHub Actions and package managers. |

## Docs

| Status | Check | Evidence | Fix |
|---|---|---|---|
| PASS | policy file | policy/default-policy.yml exists. | Keep expected repository/workflow/ref in a small policy file. |
| PASS | threat model | docs/threat-model.md exists. | Document what the pipeline does and does not prove. |
| PASS | user guide | docs/user-guide.md exists. | Add simple copy-paste verification instructions. |

## Verification

| Status | Check | Evidence | Fix |
|---|---|---|---|
| PASS | digest-only gate | Token `@sha256:` found in scripts/verify-image.sh | Reject image references that are not immutable digest references. |
| PASS | cosign verify | Token `cosign verify` found in scripts/verify-image.sh | Verify the keyless signature. |
| PASS | expected identity | Token `--certificate-identity` found in scripts/verify-image.sh | Bind the signature to the expected GitHub workflow identity. |
| PASS | OIDC issuer | Token `--certificate-oidc-issuer` found in scripts/verify-image.sh | Require GitHub's Actions OIDC issuer. |
| PASS | provenance verification | Token `gh attestation verify` found in scripts/verify-image.sh | Verify GitHub artifact attestations. |
| PASS | SBOM predicate | Token `spdx.dev` found in scripts/verify-image.sh | Require an SPDX SBOM attestation. |

## Workflow

| Status | Check | Evidence | Fix |
|---|---|---|---|
| PASS | release workflow exists | .github/workflows/secure-release.yml | Keep the release workflow under version control. |
| PASS | workflow permission: contents:read | contents:read is present in .github/workflows/secure-release.yml | Set `contents: read` in the release job permissions; it is needed to read source. |
| PASS | workflow permission: packages:write | packages:write is present in .github/workflows/secure-release.yml | Set `packages: write` in the release job permissions; it is needed to push the container image. |
| PASS | workflow permission: id-token:write | id-token:write is present in .github/workflows/secure-release.yml | Set `id-token: write` in the release job permissions; it is needed to request OIDC identity for keyless signing. |
| PASS | workflow permission: attestations:write | attestations:write is present in .github/workflows/secure-release.yml | Set `attestations: write` in the release job permissions; it is needed to publish GitHub attestations. |
| PASS | build image with Buildx | Token `docker/build-push-action` found in .github/workflows/secure-release.yml | Use docker/build-push-action so the workflow exposes the pushed digest. |
| PASS | export immutable digest | Token `steps.build.outputs.digest` found in .github/workflows/secure-release.yml | Store the digest and verify the digest reference, not a mutable tag. |
| PASS | generate SPDX SBOM | Token `anchore/sbom-action` found in .github/workflows/secure-release.yml | Generate an SBOM during the release workflow. |
| PASS | attest build provenance | Token `actions/attest-build-provenance` found in .github/workflows/secure-release.yml | Add GitHub's provenance attestation action. |
| PASS | attest SBOM | Token `actions/attest-sbom` found in .github/workflows/secure-release.yml | Add an SBOM attestation bound to the image digest. |
| PASS | cosign keyless signing | Token `cosign sign` found in .github/workflows/secure-release.yml | Sign the pushed digest with Cosign keyless signing. |
| PASS | local policy verification | Token `verify-image.sh` found in .github/workflows/secure-release.yml | Call the verification script from CI so failures are visible immediately. |
| PASS | negative deny example | Token `deny-example.sh` found in .github/workflows/secure-release.yml | Demonstrate that the policy rejects the wrong workflow identity. |
