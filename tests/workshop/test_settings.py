from copy import deepcopy
from pathlib import Path

import yaml

from workshop_tools.settings import (
    deep_merge,
    resolve_settings,
)


def test_deep_merge_merges_maps_and_replaces_lists() -> None:
    result = deep_merge(
        {
            "model": {
                "provider": "mlx",
                "options": {
                    "temperature": 0.2,
                },
            },
            "tools": ["a"],
        },
        {
            "model": {
                "options": {
                    "temperature": 0.7,
                },
            },
            "tools": ["b"],
        },
    )

    assert result == {
        "model": {
            "provider": "mlx",
            "options": {
                "temperature": 0.7,
            },
        },
        "tools": ["b"],
    }


def test_deep_merge_does_not_mutate_inputs() -> None:
    base = {
        "model": {
            "provider": "mlx",
            "options": {
                "temperature": 0.2,
            },
        },
        "tools": ["a"],
    }

    override = {
        "model": {
            "options": {
                "temperature": 0.7,
            },
        },
        "tools": ["b"],
    }

    expected_base = deepcopy(base)
    expected_override = deepcopy(override)

    deep_merge(base, override)

    assert base == expected_base
    assert override == expected_override


def test_resolve_settings_uses_canonical_precedence() -> None:
    result = resolve_settings(
        {
            "x": 0,
            "nested": {
                "a": "global",
            },
        },
        {
            "x": 1,
        },
        {
            "x": 2,
        },
        {
            "x": 3,
        },
        {
            "x": 4,
            "nested": {
                "b": "user",
            },
        },
    )

    assert result["x"] == 4

    assert result["nested"] == {
        "a": "global",
        "b": "user",
    }


def test_resolve_settings_does_not_mutate_layers() -> None:
    layers = [
        {
            "x": 0,
            "nested": {
                "global": True,
            },
        },
        {
            "x": 1,
            "nested": {
                "tenant": True,
            },
        },
        {
            "x": 2,
            "nested": {
                "workspace": True,
            },
        },
        {
            "x": 3,
            "nested": {
                "role_level": True,
            },
        },
        {
            "x": 4,
            "nested": {
                "user": True,
            },
        },
    ]

    originals = deepcopy(layers)

    resolve_settings(*layers)

    assert layers == originals


def test_workshop_settings_declare_canonical_inheritance() -> None:
    raw = yaml.safe_load(
        Path(
            "settings/workshop.yaml"
        ).read_text()
    )

    assert raw["runtimeFirst"] is True
    assert (
        raw["openWebUIRequiredForCore"]
        is False
    )

    assert raw["providerFallback"] == {
        "enabled": False,
    }

    assert raw["authorization"]["mode"] == (
        "rbac_abac"
    )

    assert raw["authorization"]["inheritance"] == [
        "global",
        "tenant",
        "workspace",
        "role_level",
        "user",
    ]


def test_granite_core_has_three_explicit_providers() -> None:
    raw = yaml.safe_load(
        Path(
            "settings/models.yaml"
        ).read_text()
    )

    granite = raw["models"]["granite.core"]

    assert granite["family"] == "ibm-granite"
    assert granite["logicalModel"] == (
        "granite-4.1-3b"
    )

    assert granite["providers"] == [
        "granite.ollama",
        "granite.mlx",
        "granite.unsloth",
    ]
