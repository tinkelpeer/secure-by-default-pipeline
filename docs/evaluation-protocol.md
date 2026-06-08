# Evaluation protocol

The thesis evaluates the prototype against a baseline GitHub Actions container release.

## Baseline

The baseline workflow builds and pushes a container image to a registry, usually with tags such as `latest` and a commit SHA. It does not require digest-only consumption, signatures, provenance attestations, or SBOM attestations.

## Proposed pipeline

The proposed pipeline builds the same image but adds:

- immutable digest reference;
- keyless Cosign signature;
- GitHub SLSA provenance attestation;
- SPDX SBOM generation;
- SBOM attestation;
- deny-by-default verification script;
- dependency review and Dependabot.

## Measurements

For each case-study repository, record:

| Metric | Baseline | Proposed pipeline | Notes |
|---|---:|---:|---|
| CI runtime in seconds | | | Use GitHub workflow duration. |
| Lines of workflow YAML | | | Count release-related YAML only. |
| Number of security artifacts | | | Signature, provenance, SBOM, SBOM attestation. |
| Digest-only verification available | no | yes/no | Should be yes for proposed. |
| Wrong workflow denied | no | yes/no | Run `deny-example.sh`. |
| SBOM available | no/yes | yes/no | Record SPDX file and attestation. |
| Maintainer steps added | | | Manual commands or configuration steps. |

## Interpretation

The evaluation should not claim that the produced image is safe. It should claim that the proposed pipeline increases verifiability, origin assurance, and dependency transparency compared with the baseline, and quantify the extra setup and CI cost.
