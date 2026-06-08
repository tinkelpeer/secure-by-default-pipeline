# Verification rule

The pipeline is deny-by-default. A container image is allowed only if all checks below pass.

1. The image reference must be immutable: `ghcr.io/<owner>/<repo>@sha256:<digest>`.
2. The image digest must have a valid Cosign keyless signature.
3. The signing certificate identity must equal `https://github.com/<owner>/<repo>/.github/workflows/secure-release.yml@refs/heads/main`.
4. The signing certificate issuer must be `https://token.actions.githubusercontent.com`.
5. A valid SLSA provenance attestation must be attached to the same image digest.
6. The provenance attestation must be signed by the expected repository, workflow, and branch.
7. A valid SPDX SBOM attestation must be attached to the same image digest.

## Why the rule is explainable

- Digest references avoid trusting mutable tags such as `latest`.
- Signatures bind the digest to a signing identity.
- Provenance says where and how the image was built.
- The SBOM says which components were present in the artifact.
- The deny example proves that "signed by someone" is not enough; the workflow identity has to match.

## What the rule does not prove

This policy proves origin, integrity of the published digest, and dependency transparency. It does not prove that every dependency was safe when the build ran. That residual risk is reduced, but not eliminated, through dependency review, pinned direct dependencies, SBOM inspection, and vulnerability scanning.
