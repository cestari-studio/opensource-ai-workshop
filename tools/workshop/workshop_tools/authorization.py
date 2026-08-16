from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AccessContext:
    tenant_id: str
    workspace_id: str
    user_id: str
    role: str
    level: int


@dataclass(frozen=True)
class Policy:
    effect: str
    permission: str
    roles: tuple[str, ...] = ()
    minimum_level: int = 0
    tenant_ids: tuple[str, ...] = ()
    workspace_ids: tuple[str, ...] = ()
    id: str | None = None


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def _matches_dimension(
    allowed: tuple[str, ...],
    actual: str,
) -> bool:
    return (
        not allowed
        or "*" in allowed
        or actual in allowed
    )


def _matches_policy(
    context: AccessContext,
    permission: str,
    policy: Policy,
) -> bool:
    if policy.permission != permission:
        return False

    if not _matches_dimension(
        policy.roles,
        context.role,
    ):
        return False

    if context.level < policy.minimum_level:
        return False

    if not _matches_dimension(
        policy.tenant_ids,
        context.tenant_id,
    ):
        return False

    if not _matches_dimension(
        policy.workspace_ids,
        context.workspace_id,
    ):
        return False

    return True


def authorize(
    context: AccessContext,
    permission: str,
    policies: list[Policy],
) -> Decision:
    matching = [
        policy
        for policy in policies
        if _matches_policy(
            context,
            permission,
            policy,
        )
    ]

    if any(
        policy.effect == "deny"
        for policy in matching
    ):
        return Decision(
            allowed=False,
            reason="explicit_deny",
        )

    if any(
        policy.effect == "allow"
        for policy in matching
    ):
        return Decision(
            allowed=True,
            reason="explicit_allow",
        )

    return Decision(
        allowed=False,
        reason="default_deny",
    )


def load_policies(
    path: Path,
) -> list[Policy]:
    raw: dict[str, Any] = (
        yaml.safe_load(path.read_text())
        or {}
    )

    result: list[Policy] = []

    for row in raw.get(
        "policies",
        [],
    ):
        effect = str(
            row["effect"]
        )

        if effect not in {
            "allow",
            "deny",
        }:
            raise ValueError(
                "invalid policy effect: "
                f"{effect}"
            )

        scope = (
            row.get("scope")
            or {}
        )

        result.append(
            Policy(
                id=(
                    str(row["id"])
                    if row.get("id")
                    is not None
                    else None
                ),
                effect=effect,
                permission=str(
                    row["permission"]
                ),
                roles=tuple(
                    str(value)
                    for value in row.get(
                        "roles",
                        [],
                    )
                ),
                minimum_level=int(
                    row.get(
                        "minimumLevel",
                        0,
                    )
                ),
                tenant_ids=tuple(
                    str(value)
                    for value in scope.get(
                        "tenantIds",
                        [],
                    )
                ),
                workspace_ids=tuple(
                    str(value)
                    for value in scope.get(
                        "workspaceIds",
                        [],
                    )
                ),
            )
        )

    return result
