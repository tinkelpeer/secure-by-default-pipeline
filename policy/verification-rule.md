# Verification Rule

## Rule

An image is allowed **only if all of the following are true**:

1. The image has a valid **Cosign signature**
2. The signature certificate identity is exactly:

   `https://github.com/<OWNER>/<REPO>/.github/workflows/ci.yml@refs/heads/main`

3. The signature certificate issuer is:

   `https://token.actions.githubusercontent.com`

4. The image has a valid **GitHub provenance attestation**
5. The provenance attestation is verified against the same repository/workflow
6. The CI run produced an SBOM artifact (`sbom.spdx.json`)

## Why this is a good demo rule

This is easy to explain:

- **Signature** proves someone signed the image
- **Keyless identity** proves *which workflow* signed it
- **Provenance** proves *how and where* it was built
- **SBOM** proves transparency of included components
- **Default deny** means anything missing one of these checks is rejected