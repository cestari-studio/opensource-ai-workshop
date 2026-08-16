from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import json
import re
from typing import Any

from .providers import ProviderProfile


class ProbeStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"


class ProbeTier(StrEnum):
    CORE = "core"
    ADVANCED = "advanced"


class CertificationStatus(StrEnum):
    CERTIFIED = "certified"
    CERTIFIED_WITH_LIMITATIONS = (
        "certified_with_limitations"
    )
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ProbeResult:
    id: str
    status: ProbeStatus
    tier: ProbeTier
    duration_ms: int
    request_summary: dict[str, Any] = field(
        default_factory=dict
    )
    response_summary: dict[str, Any] = field(
        default_factory=dict
    )
    error_class: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError(
                "probe id must not be empty"
            )

        if self.duration_ms < 0:
            raise ValueError(
                "duration_ms must be >= 0"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "tier": self.tier.value,
            "durationMs": self.duration_ms,
            "requestSummary": self.request_summary,
            "responseSummary": self.response_summary,
            "errorClass": self.error_class,
            "errorMessage": self.error_message,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CertificationDecision:
    status: CertificationStatus
    reason: str


def derive_certification(
    probes: tuple[ProbeResult, ...],
) -> CertificationDecision:
    core = sorted(
        (
            probe
            for probe in probes
            if probe.tier == ProbeTier.CORE
        ),
        key=lambda probe: probe.id,
    )

    if not core:
        raise ValueError(
            "at least one core probe is required"
        )

    unavailable_core = [
        probe.id
        for probe in core
        if probe.status == ProbeStatus.UNAVAILABLE
    ]

    if unavailable_core:
        return CertificationDecision(
            status=CertificationStatus.UNAVAILABLE,
            reason=(
                "required core probe unavailable: "
                + ", ".join(unavailable_core)
            ),
        )

    failed = sorted(
        probe.id
        for probe in probes
        if probe.status == ProbeStatus.FAIL
    )

    if failed:
        return CertificationDecision(
            status=CertificationStatus.FAILED,
            reason=(
                "probe failed: "
                + ", ".join(failed)
            ),
        )

    nonpassing_core = [
        probe.id
        for probe in core
        if probe.status != ProbeStatus.PASS
    ]

    if nonpassing_core:
        return CertificationDecision(
            status=CertificationStatus.FAILED,
            reason=(
                "required core probe did not pass: "
                + ", ".join(nonpassing_core)
            ),
        )

    advanced_unavailable = sorted(
        probe.id
        for probe in probes
        if (
            probe.tier == ProbeTier.ADVANCED
            and probe.status
            == ProbeStatus.UNAVAILABLE
        )
    )

    if advanced_unavailable:
        return CertificationDecision(
            status=CertificationStatus.FAILED,
            reason=(
                "advanced probe unavailable after "
                "core availability passed: "
                + ", ".join(advanced_unavailable)
            ),
        )

    advanced_unsupported = sorted(
        probe.id
        for probe in probes
        if (
            probe.tier == ProbeTier.ADVANCED
            and probe.status
            == ProbeStatus.UNSUPPORTED
        )
    )

    if advanced_unsupported:
        return CertificationDecision(
            status=(
                CertificationStatus
                .CERTIFIED_WITH_LIMITATIONS
            ),
            reason=(
                "advanced capability unsupported: "
                + ", ".join(
                    advanced_unsupported
                )
            ),
        )

    return CertificationDecision(
        status=CertificationStatus.CERTIFIED,
        reason="all required probes passed",
    )


_SECRET_FRAGMENTS = {
    "authorization",
    "apikey",
    "accesstoken",
    "refreshtoken",
    "token",
    "password",
    "passwd",
    "secret",
    "credential",
}


def _normalized_key(
    key: object,
) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(key).lower(),
    )


def _assert_no_secrets(
    value: Any,
    location: str = "root",
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normalized_key(key)

            if any(
                fragment in normalized
                for fragment in _SECRET_FRAGMENTS
            ):
                raise ValueError(
                    "secret-bearing key is "
                    "not permitted in receipt: "
                    f"{location}.{key}"
                )

            _assert_no_secrets(
                child,
                f"{location}.{key}",
            )

    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_secrets(
                child,
                f"{location}[{index}]",
            )


@dataclass(frozen=True)
class CertificationReceipt:
    profile: ProviderProfile
    started_at: str
    completed_at: str
    environment: dict[str, Any]
    provider_probes: tuple[
        ProbeResult,
        ...,
    ]
    mellea_probes: tuple[
        ProbeResult,
        ...,
    ] = ()
    fallback_used: bool = False
    mellea_revision: str = ""
    workshop_revision: str = ""
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.fallback_used:
            raise ValueError(
                "fallbackUsed=true is forbidden "
                "for workshop certification"
            )

        if not self.mellea_revision.strip():
            raise ValueError(
                "mellea_revision must not be empty"
            )

        if not self.workshop_revision.strip():
            raise ValueError(
                "workshop_revision must not be empty"
            )

        _assert_no_secrets(
            self.environment,
            "environment",
        )

        for probe in (
            self.provider_probes
            + self.mellea_probes
        ):
            _assert_no_secrets(
                probe.request_summary,
                (
                    f"probe.{probe.id}."
                    "requestSummary"
                ),
            )

            _assert_no_secrets(
                probe.response_summary,
                (
                    f"probe.{probe.id}."
                    "responseSummary"
                ),
            )

            _assert_no_secrets(
                probe.metadata,
                (
                    f"probe.{probe.id}."
                    "metadata"
                ),
            )

    @property
    def decision(
        self,
    ) -> CertificationDecision:
        return derive_certification(
            self.provider_probes
            + self.mellea_probes
        )

    def to_dict(
        self,
    ) -> dict[str, Any]:
        decision = self.decision

        provider_probes = sorted(
            self.provider_probes,
            key=lambda probe: probe.id,
        )

        mellea_probes = sorted(
            self.mellea_probes,
            key=lambda probe: probe.id,
        )

        return {
            "schemaVersion": self.schema_version,
            "profile": self.profile.profile,
            "provider": self.profile.provider,
            "protocol": self.profile.protocol,
            "model": {
                "logical": (
                    self.profile.model_logical
                ),
                "providerId": (
                    self.profile.model_provider_id
                ),
            },
            "endpoint": self.profile.endpoint,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "environment": self.environment,
            "providerProbes": [
                probe.to_dict()
                for probe in provider_probes
            ],
            "melleaProbes": [
                probe.to_dict()
                for probe in mellea_probes
            ],
            "certification": {
                "status": decision.status.value,
                "reason": decision.reason,
            },
            "fallbackUsed": self.fallback_used,
            "melleaRevision": (
                self.mellea_revision
            ),
            "workshopRevision": (
                self.workshop_revision
            ),
        }

    def to_json(
        self,
    ) -> str:
        return (
            json.dumps(
                self.to_dict(),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
