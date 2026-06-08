# Threat model

## Security objective

The objective is not to prove that a container image is bug-free or malware-free. The objective is to reject images that cannot be cryptographically linked to the expected GitHub repository, release workflow, branch, and dependency inventory.

The protected user is a research-software maintainer or consumer who wants a simple way to decide whether a container image should be trusted enough to run.

## Attacker capabilities

The attacker may attempt to:

1. publish a lookalike image;
2. replace a legitimate image with another digest;
3. abuse mutable tags such as `latest`;
4. introduce a malicious dependency in a pull request;
5. compromise an upstream package account or release channel;
6. modify a workflow so a release is built under weaker controls;
7. exploit the fact that consumers often do not check signatures, provenance, or SBOMs.

## Trust assumptions

The prototype assumes that GitHub Actions OIDC, Sigstore/Cosign verification, GitHub artifact attestations, and the underlying cryptographic primitives behave as intended. It does not defend against a complete compromise of those trust roots.

## Strongly mitigated threats

### Artifact substitution

A substituted image has a different digest. The verification script accepts only immutable `@sha256:` references and requires a valid signature for the expected GitHub Actions identity.

### Unauthorized publication

A third party may be able to publish a container image somewhere, but the image will not satisfy the expected certificate identity and attestation signer workflow unless it came from the approved release workflow.

### Tag confusion

The verification script refuses mutable tag references. Users must verify the digest they intend to run.

### Missing transparency

The release workflow generates an SPDX SBOM and attaches it as a signed SBOM attestation. Consumers can check that dependency metadata exists for the same digest they are verifying.

## Partially mitigated threats

### Malicious upstream dependencies

If an upstream package is malicious but the project legitimately builds it, the image may still be signed and attested. The pipeline can show what was built and from where, but it cannot magically prove that all inputs were benign. For this reason, the prototype adds dependency review, Dependabot, pinned direct dependencies, and optional vulnerability auditing.

### Malicious approved workflow changes

If maintainers review and merge a malicious workflow change, the release may still come from the expected repository. This risk has to be reduced by branch protection, review rules, and keeping the verification policy tied to a narrow workflow path.

## Residual risk

The design leaves several risks in scope for discussion but not full solution: compromised maintainers, malicious but not-yet-flagged dependencies, compromised trust roots, incomplete SBOMs, and reproducibility gaps caused by timestamps, package repositories, or mutable base images.
