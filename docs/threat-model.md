# Threat model for the secure-by-default pipeline

This document translates the thesis proposal into a concrete threat model for the prototype pipeline.

## Security objective

The main goal is **not** to prove that software is bug-free or malware-free.

The goal is narrower and more realistic:

> only allow container images that can be cryptographically linked to the expected repository, workflow, and build context, and reject images that lack verifiable provenance.

## Attacker model

The attacker may be able to:

1. publish or distribute an alternative image under a misleading name
2. try to make consumers run an image that did not come from the expected workflow
3. tamper with tags such as `latest`
4. introduce a malicious or unexpected dependency in a pull request
5. compromise an upstream package account or dependency release channel
6. exploit weak review practices around dependency or workflow changes

The attacker is **not** assumed to have full control over:

- GitHub’s OIDC issuer
- Sigstore’s trust root and transparency mechanisms
- the cryptographic verification tools themselves

## What the pipeline protects against well

### 1. Artifact substitution

Attack:
A malicious image is presented as if it were the legitimate release.

Protection:
Verification requires an immutable digest reference plus a valid Cosign keyless signature for the expected workflow identity.

Effect:
A different image digest without the right signature is rejected.

### 2. Unauthorized publication

Attack:
An attacker pushes an image to a registry or republishes a lookalike image.

Protection:
Verification checks both the Cosign signing identity and the GitHub attestation signer workflow.

Effect:
Even if the image exists in a registry, it is rejected unless it was signed and attested by the approved workflow.

### 3. Tag confusion and mutable release channels

Attack:
A consumer verifies `latest` or another mutable tag and later gets different content.

Protection:
The verification script refuses non-digest references.

Effect:
Consumers must verify `@sha256:...`, which is stable and unambiguous.

### 4. Missing transparency

Attack:
A build artifact is consumed without any dependency inventory.

Protection:
The pipeline generates an SPDX SBOM and also creates an SBOM attestation bound to the image subject.

Effect:
Consumers can verify both provenance and dependency transparency.

## What the pipeline only partially protects against

### Axios-style supply-chain compromise

Representative scenario:
A legitimate upstream dependency release is malicious, but the build itself still runs in the correct repository and workflow.

What the pipeline still guarantees:

- the image really came from the declared repository/workflow
- the image digest is authentic
- the provenance and SBOM are authentic
- the malicious dependency should become visible in the SBOM / dependency diff once known or reviewed

What the pipeline does **not** guarantee:

- that the upstream dependency was benign at build time
- that newly published malicious packages are already detected by vulnerability feeds
- that a legitimate build cannot produce a malicious result if the dependency input itself is malicious

So provenance answers:

> “Did this image come from the build process we trust?”

It does **not** answer:

> “Were all dependencies used in that build safe?”

## Extra controls added in this version for that gap

To respond to this limitation, this repo now includes:

- **dependency review on pull requests**
  - blocks merges when dependency changes introduce moderate-or-higher known vulnerabilities
- **Dependabot updates**
  - keeps Python packages and GitHub Actions under review
- **pinned Python dependencies in `requirements.txt`**
  - avoids fully floating direct dependencies

## Residual risk that remains

The prototype still does not fully solve:

- malicious dependencies that are too new to be flagged
- compromised maintainers of trusted upstream projects
- malicious workflow changes that are themselves reviewed and merged
- compromised self-hosted runners
- malicious base images if the base image reference is not digest-pinned

## Why this is a meaningful thesis prototype

This is valuable because it makes a clear security improvement over a baseline GitHub Actions release flow:

- consumers can verify **who** built the image
- consumers can verify **which workflow** built it
- consumers can verify **which git ref** built it
- consumers can verify **what dependency inventory** was declared
- consumers can reject images that do not satisfy these claims

That is a concrete, demonstrable increase in security assurance.