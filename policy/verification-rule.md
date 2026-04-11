# Verification Rule

## Rule

An image is allowed **only if all of the following are true**:

1. The image is referenced by immutable digest (`@sha256:...`)
2. The image has a valid **Cosign** signature
3. The Cosign certificate identity is exactly:

   `https://github.com/<OWNER>/<REPO>/.github/workflows/ci.yml@refs/heads/main`

4. The signature certificate issuer is:

   `https://token.actions.githubusercontent.com`

5. The image has a valid **GitHub SLSA provenance attestation**
6. The provenance attestation is verified against the same repository, workflow, and git ref
7. The image has a valid **SPDX SBOM attestation**

## Why this is a good demo rule

This is easy to explain live:

- **Signature** proves the image digest was signed
- **Keyless identity** proves *which GitHub Actions workflow* signed it
- **Provenance attestation** proves *where and how* it was built
- **SBOM attestation** proves *there is a signed dependency inventory bound to the same image subject*
- **Digest-only verification** prevents trust in mutable tags such as `latest`
- **Default deny** means anything missing one of these checks is rejected

## Important limitation

This rule proves **origin, integrity, and traceability**.
It does **not** prove that every dependency used during a legitimate build was safe.

For that residual risk, see `docs/threat-model.md`.
