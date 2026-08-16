from __future__ import annotations

from dataclasses import dataclass

from .catalog import Capability


PUBLIC_SURFACES = {
    "api",
    "cli",
    "computer",
    "openwebui",
}


@dataclass(frozen=True)
class CoverageIssue:
    code: str
    message: str


def check_coverage(
    capabilities: list[Capability],
    declared_permissions: set[str],
    source_paths: set[str],
) -> list[CoverageIssue]:
    issues: list[CoverageIssue] = []

    for capability in capabilities:
        for source_path in (
            capability.source_paths
        ):
            if source_path not in source_paths:
                issues.append(
                    CoverageIssue(
                        code="UNKNOWN_SOURCE",
                        message=(
                            f"{capability.id}: "
                            f"{source_path}"
                        ),
                    )
                )

        if not PUBLIC_SURFACES.intersection(
            capability.surfaces
        ):
            continue

        permission = (
            capability
            .authorization_permission
        )

        if permission is None:
            issues.append(
                CoverageIssue(
                    code="MISSING_PERMISSION",
                    message=capability.id,
                )
            )
            continue

        if permission not in declared_permissions:
            issues.append(
                CoverageIssue(
                    code="UNKNOWN_PERMISSION",
                    message=(
                        f"{capability.id}: "
                        f"{permission}"
                    ),
                )
            )

    return sorted(
        issues,
        key=lambda issue: (
            issue.code,
            issue.message,
        ),
    )
