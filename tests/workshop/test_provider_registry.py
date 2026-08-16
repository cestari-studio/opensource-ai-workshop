from pathlib import Path

import pytest

from workshop_tools.providers import (
    get_provider_profile,
    load_provider_registry,
)


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[2]
)


def registry():
    return load_provider_registry(
        REPOSITORY_ROOT
    )


def test_registry_loads_exact_three_profiles() -> None:
    providers = registry()

    assert list(providers) == [
        "granite.mlx",
        "granite.ollama",
        "granite.unsloth",
    ]


def test_registry_preserves_exact_provider_identity() -> None:
    providers = registry()

    ollama = providers[
        "granite.ollama"
    ]

    mlx = providers[
        "granite.mlx"
    ]

    unsloth = providers[
        "granite.unsloth"
    ]

    assert ollama.provider == "ollama"
    assert ollama.protocol == "native_mellea_ollama"
    assert ollama.model_logical == "granite-4.1-3b"
    assert ollama.model_provider_id == "granite4.1:3b"
    assert ollama.endpoint is None

    assert mlx.provider == "mlx-lm"
    assert mlx.protocol == "openai_compatible"
    assert mlx.model_logical == "granite-4.1-3b"

    assert (
        mlx.model_provider_id
        == "ibm-granite/granite-4.1-3b"
    )

    assert (
        mlx.endpoint
        == "http://127.0.0.1:8080/v1"
    )

    assert unsloth.provider == "unsloth-studio"
    assert unsloth.protocol == "openai_compatible"
    assert unsloth.model_logical == "granite-4.1-3b"

    assert (
        unsloth.model_provider_id
        == "unsloth/granite-4.1-3b-GGUF"
    )

    assert (
        unsloth.endpoint
        == "http://127.0.0.1:8888/v1"
    )


def test_registry_preserves_no_fallback_invariant() -> None:
    providers = registry()

    assert all(
        profile.fallback_enabled is False
        for profile in providers.values()
    )


def test_registry_preserves_pending_certification() -> None:
    providers = registry()

    assert {
        profile.certification_status
        for profile in providers.values()
    } == {
        "pending",
    }


def test_unknown_profile_is_rejected() -> None:
    providers = registry()

    with pytest.raises(
        KeyError,
        match="unknown provider profile",
    ):
        get_provider_profile(
            providers,
            "granite.missing",
        )
