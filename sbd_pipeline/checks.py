"""Static checks that make the security policy understandable before CI runs.

These checks do not replace cryptographic verification. They are a friendly
pre-flight checklist for maintainers: do the repository files contain the
controls that the release pipeline is supposed to enforce?
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import yaml

from .config import PipelinePolicy


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str  # pass, warn, fail
    evidence: str
    remediation: str
    category: str = "general"

    @property
    def ok(self) -> bool:
        return self.status == "pass"


WORKFLOW_HINTS = (
    ".github/workflows/secure-release.yml",
    ".github/workflows/ci.yml",
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def all_files(root: Path, pattern: str) -> list[Path]:
    return sorted(root.glob(pattern))


def find_release_workflow(root: Path, policy: PipelinePolicy) -> Path | None:
    candidates = [root / policy.workflow_path]
    candidates += [root / p for p in WORKFLOW_HINTS if p != policy.workflow_path]
    candidates += all_files(root, ".github/workflows/*.yml")
    candidates += all_files(root, ".github/workflows/*.yaml")
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            text = read_text(candidate)
            if any(token in text for token in ["attest-build-provenance", "cosign sign", "attest-sbom"]):
                return candidate
    return candidates[0] if candidates and candidates[0].exists() else None


def workflow_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def has_permission(workflow: dict, text: str, permission: str) -> bool:
    # YAML parsers treat the key "on" as boolean under YAML 1.1 in some setups;
    # the textual fallback keeps the check useful even when parsing is imperfect.
    if re.search(rf"{re.escape(permission)}\s*:\s*write", text):
        return True
    for scope in [workflow.get("permissions"), *[job.get("permissions") for job in workflow.get("jobs", {}).values() if isinstance(job, dict)]]:
        if isinstance(scope, dict) and scope.get(permission) == "write":
            return True
    return False


def check_workflow_exists(root: Path, policy: PipelinePolicy) -> CheckResult:
    workflow = find_release_workflow(root, policy)
    if workflow:
        return CheckResult("release workflow exists", "pass", str(workflow.relative_to(root)), "Keep the release workflow under version control.", "workflow")
    return CheckResult("release workflow exists", "fail", "No workflow with signing/attestation steps found.", f"Create {policy.workflow_path} from the included template.", "workflow")


def check_workflow_permissions(root: Path, policy: PipelinePolicy) -> list[CheckResult]:
    workflow_path = find_release_workflow(root, policy)
    if not workflow_path:
        return [CheckResult("workflow permissions", "fail", "No release workflow found.", "Add a release workflow first.", "workflow")]
    text = read_text(workflow_path)
    workflow = workflow_yaml(workflow_path)
    checks = []
    for permission, reason in [
        ("contents", "read source"),
        ("packages", "push the container image"),
        ("id-token", "request OIDC identity for keyless signing"),
        ("attestations", "publish GitHub attestations"),
    ]:
        wanted = "read" if permission == "contents" else "write"
        if permission == "contents":
            ok = re.search(r"contents\s*:\s*read", text) is not None
        else:
            ok = has_permission(workflow, text, permission)
        checks.append(
            CheckResult(
                f"workflow permission: {permission}:{wanted}",
                "pass" if ok else "fail",
                f"{permission}:{wanted} {'is present' if ok else 'is missing'} in {workflow_path.relative_to(root)}",
                f"Set `{permission}: {wanted}` in the release job permissions; it is needed to {reason}.",
                "workflow",
            )
        )
    return checks


def contains(text: str, *tokens: str) -> bool:
    return all(token in text for token in tokens)


def check_release_controls(root: Path, policy: PipelinePolicy) -> list[CheckResult]:
    workflow_path = find_release_workflow(root, policy)
    if not workflow_path:
        return [CheckResult("release controls", "fail", "No release workflow found.", "Add the secure-release workflow.", "workflow")]
    text = read_text(workflow_path)
    controls = [
        ("build image with Buildx", "docker/build-push-action", "Use docker/build-push-action so the workflow exposes the pushed digest."),
        ("export immutable digest", "steps.build.outputs.digest", "Store the digest and verify the digest reference, not a mutable tag."),
        ("generate SPDX SBOM", "anchore/sbom-action", "Generate an SBOM during the release workflow."),
        ("attest build provenance", "actions/attest-build-provenance", "Add GitHub's provenance attestation action."),
        ("attest SBOM", "actions/attest-sbom", "Add an SBOM attestation bound to the image digest."),
        ("cosign keyless signing", "cosign sign", "Sign the pushed digest with Cosign keyless signing."),
        ("local policy verification", "verify-image.sh", "Call the verification script from CI so failures are visible immediately."),
        ("negative deny example", "deny-example.sh", "Demonstrate that the policy rejects the wrong workflow identity."),
    ]
    return [
        CheckResult(name, "pass" if token in text else "fail", f"Token `{token}` {'found' if token in text else 'not found'} in {workflow_path.relative_to(root)}", remediation, "workflow")
        for name, token, remediation in controls
    ]


def check_verification_script(root: Path, policy: PipelinePolicy) -> list[CheckResult]:
    path = root / "scripts" / "verify-image.sh"
    text = read_text(path)
    if not text:
        return [CheckResult("verification script exists", "fail", "scripts/verify-image.sh is missing.", "Add the included verify-image.sh script.", "verification")]
    expectations = [
        ("digest-only gate", "@sha256:", "Reject image references that are not immutable digest references."),
        ("cosign verify", "cosign verify", "Verify the keyless signature."),
        ("expected identity", "--certificate-identity", "Bind the signature to the expected GitHub workflow identity."),
        ("OIDC issuer", "--certificate-oidc-issuer", "Require GitHub's Actions OIDC issuer."),
        ("provenance verification", "gh attestation verify", "Verify GitHub artifact attestations."),
        ("SBOM predicate", "spdx.dev", "Require an SPDX SBOM attestation."),
    ]
    return [
        CheckResult(name, "pass" if token in text else "fail", f"Token `{token}` {'found' if token in text else 'missing'} in {path.relative_to(root)}", remediation, "verification")
        for name, token, remediation in expectations
    ]


def requirement_is_pinned(line: str) -> bool:
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("-r "):
        return True
    return "==" in line and not any(op in line for op in [">=", "<=", "~="])


def check_python_dependencies(root: Path, policy: PipelinePolicy) -> list[CheckResult]:
    req = root / "requirements.txt"
    text = read_text(req)
    if not text:
        return [CheckResult("pinned Python dependencies", "warn", "requirements.txt not found.", "Use pinned dependency files for Python projects.", "dependencies")]
    unpinned = [line.strip() for line in text.splitlines() if not requirement_is_pinned(line)]
    return [
        CheckResult(
            "pinned Python dependencies",
            "pass" if not unpinned else "fail",
            "All direct requirements use == pins." if not unpinned else "Unpinned lines: " + ", ".join(unpinned),
            "Pin direct dependencies with == and use Dependabot/dependency review for controlled updates.",
            "dependencies",
        )
    ]


def check_dockerfile(root: Path, policy: PipelinePolicy) -> list[CheckResult]:
    dockerfile = root / "Dockerfile"
    text = read_text(dockerfile)
    if not text:
        return [CheckResult("Dockerfile exists", "fail", "Dockerfile is missing.", "Add a Dockerfile for the release image.", "container")]
    from_line = next((line for line in text.splitlines() if line.strip().upper().startswith("FROM ")), "")
    user_line = next((line for line in text.splitlines() if line.strip().upper().startswith("USER ")), "")
    results = [
        CheckResult("Dockerfile exists", "pass", "Dockerfile found.", "Keep it minimal and reproducible.", "container"),
        CheckResult("non-root container user", "pass" if user_line and not user_line.endswith("root") else "fail", user_line or "No USER instruction found.", "Run the application as a non-root user in the final image.", "container"),
        CheckResult("container healthcheck", "pass" if "HEALTHCHECK" in text else "warn", "HEALTHCHECK found." if "HEALTHCHECK" in text else "No HEALTHCHECK found.", "Add a simple health check so deployment failures are visible.", "container"),
        CheckResult("base image digest pinning", "pass" if "@sha256:" in from_line else "warn", from_line or "No FROM line found.", "For stronger reproducibility, pin the base image by digest after selecting the final base.", "container"),
    ]
    return results


def check_dependency_review(root: Path, policy: PipelinePolicy) -> list[CheckResult]:
    workflows = "\n".join(read_text(p) for p in all_files(root, ".github/workflows/*.*"))
    dependabot = read_text(root / ".github" / "dependabot.yml")
    return [
        CheckResult("dependency review workflow", "pass" if "dependency-review-action" in workflows else "warn", "dependency-review-action found." if "dependency-review-action" in workflows else "No dependency-review-action workflow found.", "Add a pull-request dependency review workflow.", "dependencies"),
        CheckResult("Dependabot updates", "pass" if "package-ecosystem" in dependabot else "warn", "Dependabot config found." if dependabot else "No .github/dependabot.yml found.", "Enable Dependabot for GitHub Actions and package managers.", "dependencies"),
    ]


def check_policy_docs(root: Path, policy: PipelinePolicy) -> list[CheckResult]:
    return [
        CheckResult("policy file", "pass" if (root / "policy" / "default-policy.yml").exists() else "warn", "policy/default-policy.yml exists." if (root / "policy" / "default-policy.yml").exists() else "default-policy.yml missing.", "Keep expected repository/workflow/ref in a small policy file.", "docs"),
        CheckResult("threat model", "pass" if (root / "docs" / "threat-model.md").exists() else "warn", "docs/threat-model.md exists." if (root / "docs" / "threat-model.md").exists() else "Threat model missing.", "Document what the pipeline does and does not prove.", "docs"),
        CheckResult("user guide", "pass" if (root / "docs" / "user-guide.md").exists() else "warn", "docs/user-guide.md exists." if (root / "docs" / "user-guide.md").exists() else "User guide missing.", "Add simple copy-paste verification instructions.", "docs"),
    ]


def run_checks(root: str | Path = ".", policy: PipelinePolicy | None = None) -> list[CheckResult]:
    root = Path(root).resolve()
    policy = policy or PipelinePolicy.from_file(root / "policy" / "default-policy.yml" if (root / "policy" / "default-policy.yml").exists() else None)
    results: list[CheckResult] = []
    results.append(check_workflow_exists(root, policy))
    results.extend(check_workflow_permissions(root, policy))
    results.extend(check_release_controls(root, policy))
    results.extend(check_verification_script(root, policy))
    results.extend(check_python_dependencies(root, policy))
    results.extend(check_dockerfile(root, policy))
    results.extend(check_dependency_review(root, policy))
    results.extend(check_policy_docs(root, policy))
    return results


def summary(results: Iterable[CheckResult]) -> dict[str, int]:
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    counts["total"] = sum(counts.values())
    return counts
