"""Small Flask dashboard for non-expert pipeline inspection."""
from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .checks import CheckResult, run_checks, summary
from .config import PipelinePolicy


def policy_for(scan_root: Path) -> PipelinePolicy:
    """Load the policy from the scanned repository when it has one."""
    policy_path = scan_root / "policy" / "default-policy.yml"
    return PipelinePolicy.from_file(policy_path if policy_path.exists() else None)


def example_repositories(base_root: Path) -> list[tuple[str, str]]:
    """Return bundled local demo repositories for the dashboard selector."""
    examples_root = base_root / "examples" / "repos"
    if not examples_root.exists():
        return []
    examples: list[tuple[str, str]] = []
    for path in sorted(examples_root.iterdir()):
        if path.is_dir():
            examples.append((path.name.replace("-", " ").title(), str(path.relative_to(base_root))))
    return examples


def resolve_scan_root(base_root: Path, repo_path: str | None) -> tuple[Path, str]:
    """Resolve a dashboard repo path while keeping relative demo paths convenient."""
    raw = (repo_path or ".").strip() or "."
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = base_root / candidate
    return candidate.resolve(), raw


def checks_for(scan_root: Path) -> tuple[PipelinePolicy, list[CheckResult]]:
    """Run checks, or return one clear failure when the selected path is invalid."""
    if not scan_root.exists() or not scan_root.is_dir():
        return PipelinePolicy(), [
            CheckResult(
                "repository path exists",
                "fail",
                f"{scan_root} is not a readable directory.",
                "Choose an existing local repository path or one of the bundled examples.",
                "repository",
            )
        ]
    policy = policy_for(scan_root)
    return policy, run_checks(scan_root, policy)


def create_app(repo_root: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    root = Path(repo_root or Path.cwd()).resolve()

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "healthy"}), 200

    @app.get("/api/checks")
    def api_checks():
        scan_root, requested_repo_path = resolve_scan_root(root, request.args.get("repo_path", "."))
        policy, results = checks_for(scan_root)
        return jsonify(
            {
                "repo_path": requested_repo_path,
                "resolved_repo_path": str(scan_root),
                "summary": summary(results),
                "checks": [r.__dict__ for r in results],
                "policy": {
                    "repository": policy.repository,
                    "workflow_path": policy.workflow_path,
                    "branch": policy.branch,
                    "expected_identity": policy.expected_identity,
                },
            }
        )

    @app.route("/", methods=["GET", "POST"])
    def index():
        scan_root, selected_repo_path = resolve_scan_root(root, request.values.get("repo_path", "."))
        policy, results = checks_for(scan_root)
        verify_command = None
        deny_command = None
        image_ref = ""
        repository = policy.repository
        workflow_path = policy.workflow_path
        branch = policy.branch
        if request.method == "POST":
            image_ref = request.form.get("image_ref", "").strip()
            repository = request.form.get("repository", repository).strip()
            workflow_path = request.form.get("workflow_path", workflow_path).strip()
            branch = request.form.get("branch", branch).strip()
            if image_ref and repository:
                verify_command = f"./scripts/verify-image.sh {image_ref} {repository} {workflow_path} {branch}"
                deny_command = f"./scripts/deny-example.sh {image_ref} {repository}"
        return render_template(
            "index.html",
            policy=policy,
            results=results,
            counts=summary(results),
            verify_command=verify_command,
            deny_command=deny_command,
            image_ref=image_ref,
            repository=repository,
            workflow_path=workflow_path,
            branch=branch,
            selected_repo_path=selected_repo_path,
            resolved_repo_path=scan_root,
            example_repositories=example_repositories(root),
        )

    return app


def main() -> None:
    create_app().run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
