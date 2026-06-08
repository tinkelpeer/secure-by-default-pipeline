from pathlib import Path

from sbd_pipeline.checks import requirement_is_pinned, run_checks, summary
from sbd_pipeline.config import PipelinePolicy


def test_default_policy_identity():
    policy = PipelinePolicy(repository="alice/project", workflow_path=".github/workflows/secure-release.yml", branch="main")
    assert policy.expected_identity == "https://github.com/alice/project/.github/workflows/secure-release.yml@refs/heads/main"
    assert policy.expected_signer_workflow == "alice/project/.github/workflows/secure-release.yml"
    assert policy.expected_source_ref == "refs/heads/main"


def test_requirement_pinning():
    assert requirement_is_pinned("Flask==3.1.3")
    assert not requirement_is_pinned("Flask>=3")
    assert not requirement_is_pinned("Flask")
    assert requirement_is_pinned("# comment")
    assert requirement_is_pinned("-r requirements.txt")


def test_repository_has_no_failing_static_checks():
    root = Path(__file__).resolve().parents[1]
    results = run_checks(root)
    counts = summary(results)
    failures = [r for r in results if r.status == "fail"]
    assert counts["pass"] >= 20
    assert not failures, "Unexpected failing checks: " + ", ".join(f.name for f in failures)
