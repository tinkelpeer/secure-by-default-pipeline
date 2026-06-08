"""Formatting utilities for command-line and Markdown reports."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable

from .checks import CheckResult, summary


def to_dicts(results: Iterable[CheckResult]) -> list[dict[str, str]]:
    return [result.__dict__.copy() for result in results]


def as_json(results: list[CheckResult]) -> str:
    return json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "summary": summary(results), "checks": to_dicts(results)}, indent=2)


def as_markdown(results: list[CheckResult]) -> str:
    counts = summary(results)
    lines = [
        "# Secure-by-default pipeline check report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Summary: **{counts['pass']} pass**, **{counts['warn']} warn**, **{counts['fail']} fail** out of {counts['total']} checks.",
        "",
    ]
    grouped: dict[str, list[CheckResult]] = defaultdict(list)
    for result in results:
        grouped[result.category].append(result)
    icons = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
    for category in sorted(grouped):
        lines += [f"## {category.title()}", "", "| Status | Check | Evidence | Fix |", "|---|---|---|---|"]
        for result in grouped[category]:
            lines.append(f"| {icons[result.status]} | {result.name} | {result.evidence} | {result.remediation} |")
        lines.append("")
    return "\n".join(lines)


def as_table(results: list[CheckResult]) -> str:
    width = max(len(r.name) for r in results) if results else 10
    lines = []
    for result in results:
        lines.append(f"{result.status.upper():<5} {result.name:<{width}}  {result.evidence}")
    counts = summary(results)
    lines.append("")
    lines.append(f"Summary: {counts['pass']} pass, {counts['warn']} warn, {counts['fail']} fail, {counts['total']} total")
    return "\n".join(lines)
