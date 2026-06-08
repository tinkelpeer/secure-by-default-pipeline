"""Command line interface for the thesis pipeline checker."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .checks import run_checks, summary
from .config import PipelinePolicy
from .report import as_json, as_markdown, as_table


def cmd_check(args: argparse.Namespace) -> int:
    policy = PipelinePolicy.from_file(args.policy) if args.policy else None
    results = run_checks(args.repo, policy)
    if args.format == "json":
        output = as_json(results)
    elif args.format == "markdown":
        output = as_markdown(results)
    else:
        output = as_table(results)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    counts = summary(results)
    return 1 if counts["fail"] else 0


def cmd_doctor(args: argparse.Namespace) -> int:
    tools = ["git", "docker", "gh", "cosign", "jq"]
    missing = [tool for tool in tools if shutil.which(tool) is None]
    if missing:
        print("Missing tools: " + ", ".join(missing))
        print("Install missing tools before running real cryptographic verification.")
        return 1
    print("All external verification tools are available.")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    script = Path(args.repo) / "scripts" / "verify-image.sh"
    if not script.exists():
        print(f"Verification script not found: {script}", file=sys.stderr)
        return 1
    cmd = [str(script), args.image_ref, args.repository, args.workflow_path, args.branch]
    return subprocess.call(cmd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sbd-check", description="Check and verify a secure-by-default container pipeline.")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Run static repository checks and print a simple report.")
    check.add_argument("--repo", default=".", help="Repository root to inspect.")
    check.add_argument("--policy", default=None, help="Optional policy YAML file.")
    check.add_argument("--format", choices=["table", "json", "markdown"], default="table")
    check.add_argument("--output", help="Write the report to a file instead of stdout.")
    check.set_defaults(func=cmd_check)

    doctor = sub.add_parser("doctor", help="Check whether external verification tools are installed.")
    doctor.set_defaults(func=cmd_doctor)

    verify = sub.add_parser("verify", help="Run scripts/verify-image.sh for a pushed digest reference.")
    verify.add_argument("image_ref", help="Immutable image reference, e.g. ghcr.io/owner/repo@sha256:...")
    verify.add_argument("repository", help="Expected GitHub repository, e.g. owner/repo")
    verify.add_argument("--repo", default=".", help="Local repository root containing scripts/verify-image.sh")
    verify.add_argument("--workflow-path", default=".github/workflows/secure-release.yml")
    verify.add_argument("--branch", default="main")
    verify.set_defaults(func=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
