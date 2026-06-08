# User guide

This project has two parts:

1. a secure release workflow that builds, signs, attests, and verifies a container image;
2. a simple checker/dashboard that explains whether the repository contains the expected controls.

## Local static check

```bash
python -m pip install -r requirements-dev.txt
python -m sbd_pipeline.cli check --repo . --format table
```

For a Markdown report:

```bash
python -m sbd_pipeline.cli check --repo . --format markdown --output secure-pipeline-report.md
```

## Dashboard

```bash
python -m pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:8080`.

The dashboard is deliberately simple. It uses green, orange, and red status rows and gives copy-paste verification commands. It is not a replacement for real cryptographic verification.

## GitHub release flow

1. Push the repository to GitHub.
2. Enable GitHub Actions.
3. Enable GitHub Packages for the repository if needed.
4. Push to `main` or run the `secure-release` workflow manually.
5. Copy the immutable image reference from the workflow summary.
6. Verify the digest locally or in another pipeline:

```bash
./scripts/verify-image.sh ghcr.io/<owner>/<repo>@sha256:<digest> <owner>/<repo> .github/workflows/secure-release.yml main
```

## Deny test

Run this to prove the policy rejects the wrong workflow identity:

```bash
./scripts/deny-example.sh ghcr.io/<owner>/<repo>@sha256:<digest> <owner>/<repo>
```

Expected result: `DENY`.

## Evidence collection

```bash
OUT_DIR=evidence ./scripts/collect-evidence.sh ghcr.io/<owner>/<repo>@sha256:<digest> <owner>/<repo>
```

This writes logs and selected attestation claims into `evidence/` for thesis evaluation.
