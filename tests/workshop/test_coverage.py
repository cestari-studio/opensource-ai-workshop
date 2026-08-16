import json
from pathlib import Path

import yaml

from workshop_tools.catalog import (
    Capability,
    load_capability_catalog,
)
from workshop_tools.coverage import (
    CoverageIssue,
    check_coverage,
)


def capability(
    *,
    permission: str | None = "generation.invoke",
    source_paths: tuple[str, ...] = (
        "mellea/stdlib/session.py",
    ),
    surfaces: tuple[str, ...] = (
        "api",
    ),
) -> Capability:
    return Capability(
        id="generation.instruct",
        domain="generation",
        status="WORKSHOP_ADAPTED",
        source_paths=source_paths,
        surfaces=surfaces,
        evidence={
            "source": True,
        },
        authorization_permission=permission,
    )


def test_unknown_permission_fails_coverage() -> None:
    issues = check_coverage(
        [capability()],
        declared_permissions={
            "other.permission",
        },
        source_paths={
            "mellea/stdlib/session.py",
        },
    )

    assert issues == [
        CoverageIssue(
            code="UNKNOWN_PERMISSION",
            message=(
                "generation.instruct: "
                "generation.invoke"
            ),
        )
    ]


def test_unknown_source_fails_coverage() -> None:
    issues = check_coverage(
        [
            capability(
                source_paths=(
                    "missing.py",
                )
            )
        ],
        declared_permissions={
            "generation.invoke",
        },
        source_paths={
            "mellea/stdlib/session.py",
        },
    )

    assert issues == [
        CoverageIssue(
            code="UNKNOWN_SOURCE",
            message=(
                "generation.instruct: "
                "missing.py"
            ),
        )
    ]


def test_public_capability_without_permission_fails() -> None:
    issues = check_coverage(
        [
            capability(
                permission=None,
            )
        ],
        declared_permissions=set(),
        source_paths={
            "mellea/stdlib/session.py",
        },
    )

    assert issues == [
        CoverageIssue(
            code="MISSING_PERMISSION",
            message="generation.instruct",
        )
    ]


def test_python_only_capability_does_not_require_permission() -> None:
    issues = check_coverage(
        [
            capability(
                permission=None,
                surfaces=("python",),
            )
        ],
        declared_permissions=set(),
        source_paths={
            "mellea/stdlib/session.py",
        },
    )

    assert issues == []


def test_valid_capability_passes_coverage() -> None:
    issues = check_coverage(
        [capability()],
        declared_permissions={
            "generation.invoke",
        },
        source_paths={
            "mellea/stdlib/session.py",
        },
    )

    assert issues == []


def test_issue_order_is_deterministic() -> None:
    issues = check_coverage(
        [
            capability(
                permission="unknown.permission",
                source_paths=(
                    "z-missing.py",
                    "a-missing.py",
                ),
            )
        ],
        declared_permissions=set(),
        source_paths=set(),
    )

    assert issues == sorted(
        issues,
        key=lambda issue: (
            issue.code,
            issue.message,
        ),
    )


def test_real_foundation_authority_passes_coverage() -> None:
    manifest = json.loads(
        Path(
            "authority/mellea/"
            "source-manifest.json"
        ).read_text()
    )

    source_paths = {
        row["path"]
        for row in manifest["entries"]
    }

    permissions_raw = yaml.safe_load(
        Path(
            "settings/authorization/"
            "permissions.yaml"
        ).read_text()
    )

    declared_permissions = set(
        permissions_raw["permissions"]
    )

    capabilities = load_capability_catalog(
        Path(
            "authority/mellea/"
            "capability-catalog.yaml"
        )
    )

    issues = check_coverage(
        capabilities,
        declared_permissions,
        source_paths,
    )

    assert issues == []


def test_coverage_policy_declares_blocking_invariants() -> None:
    policy = yaml.safe_load(
        Path(
            "authority/mellea/"
            "coverage-policy.yaml"
        ).read_text()
    )

    assert policy[
        "publicSurfaces"
    ] == [
        "api",
        "cli",
        "computer",
        "openwebui",
    ]

    assert policy[
        "blockingIssues"
    ] == [
        "MISSING_PERMISSION",
        "UNKNOWN_PERMISSION",
        "UNKNOWN_SOURCE",
    ]

    assert policy[
        "inputs"
    ] == {
        "sourceManifest": (
            "authority/mellea/"
            "source-manifest.json"
        ),
        "capabilityCatalog": (
            "authority/mellea/"
            "capability-catalog.yaml"
        ),
        "permissions": (
            "settings/authorization/"
            "permissions.yaml"
        ),
    }
