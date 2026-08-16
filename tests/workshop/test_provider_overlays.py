from pathlib import Path

import yaml


PROVIDER_NAMES = (
    "ollama",
    "mlx",
    "unsloth",
)


def load_provider(name: str) -> dict:
    return yaml.safe_load(
        Path(
            f"settings/providers/{name}.yaml"
        ).read_text()
    )


def load_models() -> dict:
    return yaml.safe_load(
        Path(
            "settings/models.yaml"
        ).read_text()
    )


def test_provider_profiles_are_unique_and_no_fallback() -> None:
    docs = [
        load_provider(name)
        for name in PROVIDER_NAMES
    ]

    profiles = [
        doc["profile"]
        for doc in docs
    ]

    assert profiles == [
        "granite.ollama",
        "granite.mlx",
        "granite.unsloth",
    ]

    assert len(profiles) == len(
        set(profiles)
    )

    for doc in docs:
        assert doc["fallback"] == {
            "enabled": False,
        }


def test_model_registry_references_exact_provider_profiles() -> None:
    models = load_models()

    configured = models[
        "models"
    ][
        "granite.core"
    ][
        "providers"
    ]

    actual = [
        load_provider(name)["profile"]
        for name in PROVIDER_NAMES
    ]

    assert actual == configured


def test_all_profiles_are_granite_4_1_3b() -> None:
    for name in PROVIDER_NAMES:
        model = load_provider(
            name
        )["model"]

        assert (
            model["family"]
            == "ibm-granite"
        )

        assert (
            model["logical"]
            == "granite-4.1-3b"
        )


def test_ollama_profile_is_explicit() -> None:
    doc = load_provider(
        "ollama"
    )

    assert doc["provider"] == "ollama"

    assert (
        doc["model"]["providerId"]
        == "granite4.1:3b"
    )

    assert (
        doc["protocol"]
        == "native_mellea_ollama"
    )

    assert "endpoint" not in doc


def test_mlx_profile_is_explicit() -> None:
    doc = load_provider(
        "mlx"
    )

    assert doc["provider"] == "mlx-lm"

    assert (
        doc["model"]["providerId"]
        == "ibm-granite/granite-4.1-3b"
    )

    assert (
        doc["protocol"]
        == "openai_compatible"
    )

    assert (
        doc["endpoint"]
        == "http://127.0.0.1:8080/v1"
    )


def test_unsloth_profile_is_explicit() -> None:
    doc = load_provider(
        "unsloth"
    )

    assert (
        doc["provider"]
        == "unsloth-studio"
    )

    assert (
        doc["model"]["providerId"]
        == "unsloth/granite-4.1-3b-GGUF"
    )

    assert (
        doc["protocol"]
        == "openai_compatible"
    )

    assert (
        doc["endpoint"]
        == "http://127.0.0.1:8888/v1"
    )


def test_provider_overlays_do_not_mutate_mellea() -> None:
    for name in PROVIDER_NAMES:
        overlay = load_provider(
            name
        )["overlay"]

        assert (
            overlay["owner"]
            == "workshop"
        )

        assert (
            overlay[
                "mutatesMelleaModelIdentifier"
            ]
            is False
        )


def test_certification_starts_pending() -> None:
    for name in PROVIDER_NAMES:
        certification = load_provider(
            name
        )["certification"]

        assert (
            certification["status"]
            == "pending"
        )

        assert (
            certification["providerCertified"]
            is False
        )
