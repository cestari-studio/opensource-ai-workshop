from __future__ import annotations

from copy import deepcopy
from typing import Any


Settings = dict[str, Any]


def deep_merge(
    base: Settings,
    override: Settings,
) -> Settings:
    """Merge settings deterministically.

    Rules:
    - mappings merge recursively;
    - lists replace;
    - scalar values replace;
    - neither input is mutated.
    """

    result = deepcopy(base)

    for key, value in override.items():
        current = result.get(key)

        if (
            isinstance(value, dict)
            and isinstance(current, dict)
        ):
            result[key] = deep_merge(
                current,
                value,
            )
        else:
            result[key] = deepcopy(value)

    return result


def resolve_settings(
    global_defaults: Settings,
    tenant: Settings,
    workspace: Settings,
    role_level: Settings,
    user: Settings,
) -> Settings:
    """Resolve canonical workshop settings precedence.

    Precedence, lowest to highest:

    global
      -> tenant
      -> workspace
      -> role/level
      -> user
    """

    result = deepcopy(global_defaults)

    for layer in (
        tenant,
        workspace,
        role_level,
        user,
    ):
        result = deep_merge(
            result,
            layer,
        )

    return result
