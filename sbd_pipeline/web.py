"""Small Flask dashboard for non-expert pipeline inspection."""
from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .checks import run_checks, summary
from .config import PipelinePolicy


def create_app(repo_root: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    root = Path(repo_root or Path.cwd()).resolve()

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "healthy"}), 200

    @app.get("/api/checks")
    def api_checks():
        policy = PipelinePolicy.from_file(root / "policy" / "default-policy.yml" if (root / "policy" / "default-policy.yml").exists() else None)
        results = run_checks(root, policy)
        return jsonify({"summary": summary(results), "checks": [r.__dict__ for r in results]})

    @app.route("/", methods=["GET", "POST"])
    def index():
        policy = PipelinePolicy.from_file(root / "policy" / "default-policy.yml" if (root / "policy" / "default-policy.yml").exists() else None)
        results = run_checks(root, policy)
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
        )

    return app


def main() -> None:
    create_app().run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
