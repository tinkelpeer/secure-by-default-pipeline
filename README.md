# Secure-by-default supply-chain pipeline for containerised research software

This repository is the thesis prototype: a small, opinionated reference pipeline for GitHub repositories that build OCI-compatible container images. It is designed to be easy to inspect, easy to explain, and strict enough to reject images that do not have verifiable origin and dependency transparency.

## What this repository gives you

- A GitHub Actions release workflow that builds and pushes a container image to GHCR.
- An SPDX SBOM for the pushed image.
- A GitHub SLSA provenance attestation.
- A GitHub SBOM attestation.
- A Cosign keyless signature bound to the GitHub Actions workflow identity.
- A deny-by-default verification script.
- A small CLI and web dashboard for checking whether the repository contains the expected controls.
- Documentation for the threat model, verification policy, user guide, and evaluation protocol.

## The simple rule

Do not run an image unless all of the following are true:

1. You are verifying an immutable digest reference, not a mutable tag.
2. The digest has a valid Cosign keyless signature.
3. The signing identity is the expected GitHub Actions workflow.
4. The image has a valid provenance attestation from the expected repository/workflow/ref.
5. The same image has a valid SPDX SBOM attestation.

That is the thesis prototype in one sentence: **make unsigned, unauthenticated, or undocumented images fail by default**.

## Quick start for maintainers

Install and run the local checker:

```bash
python -m pip install -r requirements-dev.txt
python -m sbd_pipeline.cli check --repo . --format table
```

Generate a report:

```bash
python -m sbd_pipeline.cli check --repo . --format markdown --output secure-pipeline-report.md
```

Run the dashboard:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8080`.

## How to use the release pipeline

1. Push this repository to GitHub.
2. Adjust `policy/default-policy.yml` so `repository` matches `owner/repo`.
3. Enable Actions and packages.
4. Push to `main` or manually run the `secure-release` workflow.
5. Copy the immutable image reference from the workflow summary.
6. Verify the release:

```bash
./scripts/verify-image.sh \
  ghcr.io/<owner>/<repo>@sha256:<digest> \
  <owner>/<repo> \
  .github/workflows/secure-release.yml \
  main
```

7. Prove the deny rule works:

```bash
./scripts/deny-example.sh ghcr.io/<owner>/<repo>@sha256:<digest> <owner>/<repo>
```

Expected result: `DENY`.

## Repository map

```text
.github/workflows/secure-release.yml  build, sign, attest, verify
.github/workflows/checks.yml          tests and static policy checks
.github/workflows/dependency-review.yml dependency review on PRs
sbd_pipeline/                         CLI and dashboard source code
scripts/verify-image.sh               real cryptographic verification
scripts/deny-example.sh               negative policy test
policy/default-policy.yml             expected repository/workflow/ref
docs/threat-model.md                  attacker model and residual risk
docs/user-guide.md                    copy-paste usage instructions
docs/evaluation-protocol.md           thesis measurement plan
tests/                                unit tests for the checker
```

## What the pipeline protects against

It protects well against artifact substitution, tag confusion, unauthorized publication from the wrong workflow identity, and missing dependency transparency.

It only partially protects against malicious upstream dependencies. If a legitimate workflow builds a malicious dependency, provenance still proves that the expected workflow built the image; it does not prove that all inputs were safe. That is why this repository also includes dependency review, Dependabot, pinned direct dependencies, and clear residual-risk documentation.

## Development

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python -m sbd_pipeline.cli check --repo . --format table
```
