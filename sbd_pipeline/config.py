"""Configuration helpers for the secure-by-default pipeline checker."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PipelinePolicy:
    """Expected release policy for a container image.

    The default values mirror the GitHub + GHCR workflow used in the thesis
    prototype. Users can override the values in policy/default-policy.yml.
    """

    repository: str = "OWNER/REPO"
    workflow_path: str = ".github/workflows/secure-release.yml"
    branch: str = "main"
    image_registry: str = "ghcr.io"
    sbom_predicate_types: tuple[str, ...] = (
        "https://spdx.dev/Document/v2.3",
        "https://spdx.dev/Document",
    )
    provenance_predicate_type: str = "https://slsa.dev/provenance/v1"
    required_controls: tuple[str, ...] = (
        "immutable_digest",
        "cosign_keyless_signature",
        "provenance_attestation",
        "sbom_attestation",
        "deny_by_default_verification",
        "dependency_review",
        "pinned_dependencies",
        "non_root_container",
    )

    @classmethod
    def from_file(cls, path: str | Path | None) -> "PipelinePolicy":
        if path is None:
            return cls()
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        # Allow a top-level "policy" wrapper because it reads better in YAML.
        data = data.get("policy", data)
        kwargs: dict[str, Any] = {}
        for key in cls.__dataclass_fields__:
            if key in data:
                value = data[key]
                if key in {"required_controls", "sbom_predicate_types"}:
                    value = tuple(value)
                kwargs[key] = value
        return cls(**kwargs)

    @property
    def expected_identity(self) -> str:
        return f"https://github.com/{self.repository}/{self.workflow_path}@refs/heads/{self.branch}"

    @property
    def expected_signer_workflow(self) -> str:
        return f"{self.repository}/{self.workflow_path}"

    @property
    def expected_source_ref(self) -> str:
        return f"refs/heads/{self.branch}"
