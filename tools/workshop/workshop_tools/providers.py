from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProviderProfile:
    profile: str
    provider: str
    protocol: str
    model_logical: str
    model_provider_id: str
    endpoint: str | None = None
    fallback_enabled: bool = False
    certification_status: str = "pending"
    provider_certified: bool = False
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        required = {
            "profile": self.profile,
            "provider": self.provider,
            "protocol": self.protocol,
            "model_logical": self.model_logical,
            "model_provider_id": self.model_provider_id,
            "schema_version": self.schema_version,
            "certification_status": (
                self.certification_status
            ),
        }

        for name, value in required.items():
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )

        if self.fallback_enabled:
            raise ValueError(
                "provider fallback must be disabled"
            )


def _mapping(
    value: Any,
    *,
    field: str,
    source: Path,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(
            f"{field} must be a mapping: {source}"
        )

    return value


def _required_string(
    mapping: dict[str, Any],
    key: str,
    *,
    source: Path,
) -> str:
    value = mapping.get(key)

    if not isinstance(value, str):
        raise ValueError(
            f"{key} must be a string: {source}"
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{key} must not be empty: {source}"
        )

    return value


def _load_provider_file(
    source: Path,
) -> ProviderProfile:
    raw = (
        yaml.safe_load(
            source.read_text()
        )
        or {}
    )

    data = _mapping(
        raw,
        field="provider overlay",
        source=source,
    )

    schema_version = _required_string(
        data,
        "schemaVersion",
        source=source,
    )

    if schema_version != "1.0.0":
        raise ValueError(
            "unsupported provider schemaVersion "
            f"{schema_version!r}: {source}"
        )

    model = _mapping(
        data.get("model"),
        field="model",
        source=source,
    )

    fallback = _mapping(
        data.get("fallback"),
        field="fallback",
        source=source,
    )

    certification = _mapping(
        data.get("certification"),
        field="certification",
        source=source,
    )

    fallback_enabled = fallback.get(
        "enabled"
    )

    if not isinstance(
        fallback_enabled,
        bool,
    ):
        raise ValueError(
            "fallback.enabled must be boolean: "
            f"{source}"
        )

    if fallback_enabled:
        raise ValueError(
            "provider fallback must be disabled: "
            f"{source}"
        )

    provider_certified = certification.get(
        "providerCertified"
    )

    if not isinstance(
        provider_certified,
        bool,
    ):
        raise ValueError(
            "certification.providerCertified "
            f"must be boolean: {source}"
        )

    endpoint = data.get(
        "endpoint"
    )

    if endpoint is not None:
        if not isinstance(
            endpoint,
            str,
        ):
            raise ValueError(
                "endpoint must be a string "
                f"or null: {source}"
            )

        endpoint = endpoint.strip()

        if not endpoint:
            raise ValueError(
                "endpoint must not be empty: "
                f"{source}"
            )

    return ProviderProfile(
        profile=_required_string(
            data,
            "profile",
            source=source,
        ),
        provider=_required_string(
            data,
            "provider",
            source=source,
        ),
        protocol=_required_string(
            data,
            "protocol",
            source=source,
        ),
        model_logical=_required_string(
            model,
            "logical",
            source=source,
        ),
        model_provider_id=_required_string(
            model,
            "providerId",
            source=source,
        ),
        endpoint=endpoint,
        fallback_enabled=fallback_enabled,
        certification_status=_required_string(
            certification,
            "status",
            source=source,
        ),
        provider_certified=provider_certified,
        schema_version=schema_version,
    )


def load_provider_registry(
    root: str | Path,
) -> dict[str, ProviderProfile]:
    repository_root = (
        Path(root)
        .expanduser()
        .resolve()
    )

    provider_dir = (
        repository_root
        / "settings"
        / "providers"
    )

    if not provider_dir.is_dir():
        raise FileNotFoundError(
            "provider settings directory "
            f"not found: {provider_dir}"
        )

    profiles: dict[
        str,
        ProviderProfile,
    ] = {}

    sources = sorted(
        provider_dir.glob("*.yaml"),
        key=lambda path: path.name,
    )

    if not sources:
        raise ValueError(
            "no provider overlays found: "
            f"{provider_dir}"
        )

    for source in sources:
        provider = _load_provider_file(
            source
        )

        if provider.profile in profiles:
            raise ValueError(
                "duplicate provider profile: "
                f"{provider.profile}"
            )

        profiles[
            provider.profile
        ] = provider

    return dict(
        sorted(
            profiles.items()
        )
    )


def get_provider_profile(
    registry: dict[
        str,
        ProviderProfile,
    ],
    profile: str,
) -> ProviderProfile:
    try:
        return registry[profile]
    except KeyError:
        raise KeyError(
            "unknown provider profile: "
            f"{profile}"
        ) from None
