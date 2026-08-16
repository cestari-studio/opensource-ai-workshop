from pathlib import Path

import yaml

from workshop_tools.authorization import (
    AccessContext,
    Policy,
    authorize,
    load_policies,
)
from workshop_tools.catalog import (
    load_capability_catalog,
)


def ctx(**overrides) -> AccessContext:
    base = {
        "tenant_id": "tenant-master",
        "workspace_id": "workspace-dev",
        "user_id": "user-1",
        "role": "developer",
        "level": 30,
    }

    base.update(overrides)

    return AccessContext(**base)


def test_default_deny() -> None:
    decision = authorize(
        ctx(),
        "generation.invoke",
        [],
    )

    assert decision.allowed is False
    assert decision.reason == "default_deny"


def test_matching_allow() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="generation.invoke",
            roles=("developer",),
            minimum_level=20,
        )
    ]

    decision = authorize(
        ctx(),
        "generation.invoke",
        policies,
    )

    assert decision.allowed is True
    assert decision.reason == "explicit_allow"


def test_deny_wins_over_matching_allow() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="tools.shell.execute",
            roles=("developer",),
            minimum_level=20,
        ),
        Policy(
            effect="deny",
            permission="tools.shell.execute",
            roles=("developer",),
            minimum_level=0,
        ),
    ]

    decision = authorize(
        ctx(),
        "tools.shell.execute",
        policies,
    )

    assert decision.allowed is False
    assert decision.reason == "explicit_deny"


def test_minimum_level_is_enforced() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="admin.settings.write",
            roles=("workspace_admin",),
            minimum_level=80,
        )
    ]

    decision = authorize(
        ctx(
            role="workspace_admin",
            level=50,
        ),
        "admin.settings.write",
        policies,
    )

    assert decision.allowed is False
    assert decision.reason == "default_deny"


def test_matching_tenant_and_workspace_scope_allows() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="generation.invoke",
            roles=("developer",),
            minimum_level=20,
            tenant_ids=("tenant-master",),
            workspace_ids=("workspace-dev",),
        )
    ]

    assert (
        authorize(
            ctx(),
            "generation.invoke",
            policies,
        ).allowed
        is True
    )


def test_tenant_scope_mismatch_denies() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="generation.invoke",
            roles=("developer",),
            minimum_level=20,
            tenant_ids=("tenant-other",),
        )
    ]

    decision = authorize(
        ctx(),
        "generation.invoke",
        policies,
    )

    assert decision.allowed is False
    assert decision.reason == "default_deny"


def test_workspace_scope_mismatch_denies() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="generation.invoke",
            roles=("developer",),
            minimum_level=20,
            workspace_ids=("workspace-other",),
        )
    ]

    decision = authorize(
        ctx(),
        "generation.invoke",
        policies,
    )

    assert decision.allowed is False
    assert decision.reason == "default_deny"


def test_permission_mismatch_denies() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="documents.process",
            roles=("developer",),
            minimum_level=20,
        )
    ]

    assert (
        authorize(
            ctx(),
            "generation.invoke",
            policies,
        ).allowed
        is False
    )


def test_wildcard_scope_matches() -> None:
    policies = [
        Policy(
            effect="allow",
            permission="generation.invoke",
            roles=("*",),
            minimum_level=0,
            tenant_ids=("*",),
            workspace_ids=("*",),
        )
    ]

    assert (
        authorize(
            ctx(),
            "generation.invoke",
            policies,
        ).allowed
        is True
    )


def test_authorization_settings_cover_catalog_permissions() -> None:
    permissions_raw = yaml.safe_load(
        Path(
            "settings/authorization/"
            "permissions.yaml"
        ).read_text()
    )

    known_permissions = set(
        permissions_raw["permissions"]
    )

    capabilities = load_capability_catalog(
        Path(
            "authority/mellea/"
            "capability-catalog.yaml"
        )
    )

    required_permissions = {
        capability.authorization_permission
        for capability in capabilities
        if capability.authorization_permission
        is not None
    }

    assert required_permissions <= known_permissions


def test_policy_settings_reference_known_roles_and_permissions() -> None:
    roles_raw = yaml.safe_load(
        Path(
            "settings/authorization/"
            "roles.yaml"
        ).read_text()
    )

    permissions_raw = yaml.safe_load(
        Path(
            "settings/authorization/"
            "permissions.yaml"
        ).read_text()
    )

    known_roles = set(
        roles_raw["roles"]
    )

    known_permissions = set(
        permissions_raw["permissions"]
    )

    policies = load_policies(
        Path(
            "settings/authorization/"
            "policies.yaml"
        )
    )

    assert policies

    for policy in policies:
        assert policy.effect in {
            "allow",
            "deny",
        }

        assert (
            policy.permission
            in known_permissions
        )

        assert set(policy.roles) - {
            "*"
        } <= known_roles

        assert (
            0
            <= policy.minimum_level
            <= 100
        )


def test_baseline_developer_entitlements() -> None:
    policies = load_policies(
        Path(
            "settings/authorization/"
            "policies.yaml"
        )
    )

    developer = ctx()

    assert authorize(
        developer,
        "generation.invoke",
        policies,
    ).allowed is True

    assert authorize(
        developer,
        "generation.codegen",
        policies,
    ).allowed is True

    assert authorize(
        developer,
        "documents.process",
        policies,
    ).allowed is True

    assert authorize(
        developer,
        "tools.mcp.invoke",
        policies,
    ).allowed is True

    assert authorize(
        developer,
        "tools.shell.execute",
        policies,
    ).allowed is False
