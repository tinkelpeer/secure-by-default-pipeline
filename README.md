# Secure-by-Default Container Supply Chain Pipeline

This repository is an iteration of a secure-by-default container pipeline.

It demonstrates how a container image can be built, signed, attested, and verified with an explicit deny-by-default policy based on build identity and immutable image digests.

## What this version changes

This version introduces several structural improvements:

1. **Consistent SBOM handling**
   - exactly one SBOM file is generated: `sbom.spdx.json`
   - the uploaded GitHub artifact uses the same filename
   - the same SBOM is also attested, so its relation to the image can be verified cryptographically

2. **Reduced build-artifact ambiguity**
   - Docker Buildx can upload a build record artifact by default
   - this workflow disables that upload using `DOCKER_BUILD_RECORD_UPLOAD=false`
   - the pipeline output is therefore limited to the intended security-relevant artifacts

3. **Reproducible verification**
   - verification checks three artifact classes:
     - Cosign signature
     - GitHub provenance attestation
     - GitHub SBOM attestation
   - the verification script validates the expected workflow path and branch explicitly

4. **Explicit allow and deny behavior**
   - the workflow includes a successful verification case
   - it also includes a negative verification case using the wrong workflow identity
   - this demonstrates that policy evaluation depends on the expected build identity, not only on the existence of a signature

5. **More explicit threat-model scope**
   - a pull-request dependency review workflow is included
   - Dependabot is configured for Python dependencies and GitHub Actions
   - the repository distinguishes between threats that provenance mitigates and threats it only partially addresses

## What the pipeline produces

For every push to `main`, the pipeline produces:

- a container image in GHCR
- one SBOM file: `sbom.spdx.json`
- one **provenance attestation** for the image
- one **SBOM attestation** bound to the image
- one **Cosign keyless signature** bound to the immutable image digest

The workflow summary also prints:

- the immutable image reference
- the provenance attestation URL
- the SBOM attestation URL
- example commands for local verification

## Security policy enforced by `verify-image.sh`

An image is allowed only if all of the following are true:

1. the image reference is immutable (`@sha256:...`)
2. a valid Cosign keyless signature exists
3. the Cosign certificate identity is exactly the expected GitHub Actions workflow
4. the OIDC issuer is `https://token.actions.githubusercontent.com`
5. a valid SLSA provenance attestation exists
6. the provenance attestation was created by the expected repository, workflow, and ref
7. a valid SPDX SBOM attestation exists for the same image

This defines a deny-by-default policy based on verifiable origin, integrity, and traceability.

## Image reference format

Verification must be performed against an immutable image digest.

Correct:

```bash
ghcr.io/tinkelpeer/secure-by-default-pipeline@sha256:<digest>
```

Incorrect:

```bash
ghcr.io/tinkelpeer/secure-by-default-pipeline:sha256-<digest>
```

Cosign signatures are attached to the image digest, not to a tag-like reference such as `:sha256-...`.

## Quick start

### 1. Push to a public GitHub repository

Push this repository to GitHub and make sure Actions are enabled.

### 2. Run the workflow on `main`

The main workflow will:

- build and push the image
- generate the SBOM
- create provenance and SBOM attestations
- sign the image with Cosign
- verify the image with the expected policy
- verify that an incorrect policy is denied

### 3. Copy the immutable digest reference from the workflow summary

The summary will contain an image reference like:

```bash
ghcr.io/<OWNER>/<REPO>@sha256:<DIGEST>
```

### 4. Verify locally

Install:

- Docker
- GitHub CLI (`gh`)
- Cosign
- `jq` (optional, only needed for the attestation inspection helper)

Run:

```bash
chmod +x scripts/*.sh
./scripts/verify-image.sh ghcr.io/<OWNER>/<REPO>@sha256:<DIGEST> <OWNER>/<REPO> .github/workflows/ci.yml main
```

Expected result:

- Cosign signature verification passes
- provenance attestation verification passes
- SBOM attestation verification passes
- final policy result is `ALLOW`

### 5. Run the deny example

```bash
./scripts/deny-example.sh ghcr.io/<OWNER>/<REPO>@sha256:<DIGEST> <OWNER>/<REPO>
```

Expected result:

- verification fails because the expected workflow identity is intentionally incorrect
- final result is `EXPECTED RESULT: DENY`

## Scripts

### `scripts/verify-image.sh`

Verifies:

- exact GitHub Actions workflow identity via Cosign certificate identity
- provenance attestation via `gh attestation verify`
- SPDX SBOM attestation via `gh attestation verify --predicate-type https://spdx.dev/Document/v2.3`

### `scripts/deny-example.sh`

Runs the same verification logic with an incorrect workflow file path and should therefore fail.

### `scripts/show-attestation-claims.sh`

Prints selected attestation claims as JSON to show which claims are being checked.

Example:

```bash
./scripts/show-attestation-claims.sh ghcr.io/<OWNER>/<REPO>@sha256:<DIGEST> <OWNER>/<REPO>
```

## Threat model summary

This pipeline mainly protects against artifact substitution, unauthorized publication, and use of images without verifiable provenance.

It does not prove that every dependency used during a legitimate build was benign.

For the full version, see [`docs/threat-model.md`](docs/threat-model.md).