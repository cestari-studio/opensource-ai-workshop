from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderProfile:
    profile: str
    provider: str
    protocol: str
    model_logical: str
    model_provider_id: str
    endpoint: str | None = None

    def __post_init__(self) -> None:
        required = {
            "profile": self.profile,
            "provider": self.provider,
            "protocol": self.protocol,
            "model_logical": self.model_logical,
            "model_provider_id": self.model_provider_id,
        }

        for name, value in required.items():
            if not value.strip():
                raise ValueError(
                    f"{name} must not be empty"
                )
