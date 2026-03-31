# Secure-by-Default Container Supply Chain Demo

This repository is a minimal prototype for a **secure-by-default container pipeline**.

It demonstrates:

1. **Container build** with GitHub Actions
2. **SBOM generation** with Syft
3. **Provenance attestation** with GitHub Artifact Attestations
4. **Image signing** with Sigstore Cosign (keyless via GitHub OIDC)
5. **Verification policy**
6. **Deny example** showing policy failure

## What gets produced

- **Built container image** in GHCR  
  Example:
  `ghcr.io/<OWNER>/<REPO>:<GIT_SHA>`
- **SBOM artifact**  
  File: `sbom.spdx.json`
- **Provenance attestation**  
  Attached to the pushed container image
- **Signature**  
  Attached to the pushed container image in the registry

## Security model

We only trust a container image if:

- it has a valid **Cosign signature**
- the signature was created by **this exact GitHub Actions workflow**
- it has a valid **GitHub provenance attestation**
- the attestation comes from **this repository**
- an SBOM exists as a CI artifact

That makes the default behavior “deny unless verified”.

## How to use

### 1. Create a public GitHub repo
Push this repository to GitHub.

### 2. Enable GitHub Container Registry permissions
The workflow pushes to:

`ghcr.io/<OWNER>/<REPO>`

### 3. Run the workflow
Push to `main`.

### 4. Verify the image locally

Install:
- Docker
- GitHub CLI (`gh`)
- Cosign

Then run:

```bash
chmod +x scripts/*.sh
./scripts/verify-image.sh ghcr.io/<OWNER>/<REPO>@sha256:<DIGEST> <OWNER>/<REPO> .github/workflows/ci.yml main