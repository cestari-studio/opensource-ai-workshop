import json

import pytest

from workshop_tools.certification import (
    CertificationReceipt,
    CertificationStatus,
    ProbeResult,
    ProbeStatus,
    ProbeTier,
    derive_certification,
)
from workshop_tools.providers import (
    ProviderProfile,
)


def profile() -> ProviderProfile:
    return ProviderProfile(
        profile="granite.mlx",
        provider="mlx-lm",
        protocol="openai_compatible",
        model_logical="granite-4.1-3b",
        model_provider_id=(
            "ibm-granite/granite-4.1-3b"
        ),
        endpoint=(
            "http://127.0.0.1:8080/v1"
        ),
    )


def probe(
    probe_id: str,
    status: ProbeStatus = ProbeStatus.PASS,
    tier: ProbeTier = ProbeTier.CORE,
) -> ProbeResult:
    return ProbeResult(
        id=probe_id,
        status=status,
        tier=tier,
        duration_ms=12,
        request_summary={
            "kind": "test",
        },
        response_summary={
            "kind": "test",
        },
        metadata={},
    )


def receipt(
    *,
    provider_probes: tuple[ProbeResult, ...],
    mellea_probes: tuple[ProbeResult, ...] = (),
    fallback_used: bool = False,
    environment: dict | None = None,
) -> CertificationReceipt:
    return CertificationReceipt(
        profile=profile(),
        started_at="2026-08-15T23:00:00-03:00",
        completed_at="2026-08-15T23:01:00-03:00",
        environment=(
            environment
            if environment is not None
            else {
                "platform": "darwin",
                "arch": "arm64",
            }
        ),
        provider_probes=provider_probes,
        mellea_probes=mellea_probes,
        fallback_used=fallback_used,
        mellea_revision=(
            "853b04fe572b3f8d2947c56750c883aeae12ea0b"
        ),
        workshop_revision="test-workshop-revision",
    )


def test_all_required_probes_pass_certifies() -> None:
    decision = derive_certification(
        (
            probe("availability"),
            probe("identity"),
            probe("generation"),
            probe(
                "structured",
                tier=ProbeTier.ADVANCED,
            ),
        )
    )

    assert (
        decision.status
        == CertificationStatus.CERTIFIED
    )


def test_advanced_unsupported_becomes_limitation() -> None:
    decision = derive_certification(
        (
            probe("availability"),
            probe("generation"),
            probe(
                "tool_calling",
                ProbeStatus.UNSUPPORTED,
                ProbeTier.ADVANCED,
            ),
        )
    )

    assert (
        decision.status
        == CertificationStatus.CERTIFIED_WITH_LIMITATIONS
    )

    assert "tool_calling" in decision.reason


def test_core_unavailable_becomes_unavailable() -> None:
    decision = derive_certification(
        (
            probe(
                "availability",
                ProbeStatus.UNAVAILABLE,
            ),
            probe(
                "generation",
                ProbeStatus.NOT_APPLICABLE,
            ),
        )
    )

    assert (
        decision.status
        == CertificationStatus.UNAVAILABLE
    )


def test_core_failure_fails_certification() -> None:
    decision = derive_certification(
        (
            probe("availability"),
            probe(
                "generation",
                ProbeStatus.FAIL,
            ),
        )
    )

    assert (
        decision.status
        == CertificationStatus.FAILED
    )


def test_core_unsupported_fails_certification() -> None:
    decision = derive_certification(
        (
            probe("availability"),
            probe(
                "generation",
                ProbeStatus.UNSUPPORTED,
            ),
        )
    )

    assert (
        decision.status
        == CertificationStatus.FAILED
    )


def test_advanced_failure_is_failure_not_limitation() -> None:
    decision = derive_certification(
        (
            probe("availability"),
            probe("generation"),
            probe(
                "tool_calling",
                ProbeStatus.FAIL,
                ProbeTier.ADVANCED,
            ),
        )
    )

    assert (
        decision.status
        == CertificationStatus.FAILED
    )


def test_advanced_not_applicable_does_not_degrade() -> None:
    decision = derive_certification(
        (
            probe("availability"),
            probe("generation"),
            probe(
                "usage_metadata",
                ProbeStatus.NOT_APPLICABLE,
                ProbeTier.ADVANCED,
            ),
        )
    )

    assert (
        decision.status
        == CertificationStatus.CERTIFIED
    )


def test_empty_evidence_cannot_certify() -> None:
    with pytest.raises(
        ValueError,
        match="at least one core probe",
    ):
        derive_certification(())


def test_fallback_used_true_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="fallbackUsed=true",
    ):
        receipt(
            provider_probes=(
                probe("availability"),
            ),
            fallback_used=True,
        )


def test_receipt_json_is_deterministic_and_sorts_probes() -> None:
    first = receipt(
        provider_probes=(
            probe("generation"),
            probe("availability"),
            probe("identity"),
        )
    )

    second = receipt(
        provider_probes=(
            probe("identity"),
            probe("generation"),
            probe("availability"),
        )
    )

    first_json = first.to_json()
    second_json = second.to_json()

    assert first_json == second_json

    data = json.loads(
        first_json
    )

    assert data["schemaVersion"] == "1.0.0"
    assert data["profile"] == "granite.mlx"
    assert data["provider"] == "mlx-lm"

    assert (
        data["protocol"]
        == "openai_compatible"
    )

    assert data["model"] == {
        "logical": "granite-4.1-3b",
        "providerId": (
            "ibm-granite/granite-4.1-3b"
        ),
    }

    assert (
        data["endpoint"]
        == "http://127.0.0.1:8080/v1"
    )

    assert data["fallbackUsed"] is False

    assert (
        data["certification"]["status"]
        == "certified"
    )

    assert [
        row["id"]
        for row in data["providerProbes"]
    ] == [
        "availability",
        "generation",
        "identity",
    ]

    assert (
        data["melleaRevision"]
        == "853b04fe572b3f8d2947c56750c883aeae12ea0b"
    )


def test_receipt_rejects_secret_material() -> None:
    with pytest.raises(
        ValueError,
        match="secret-bearing key",
    ):
        receipt(
            provider_probes=(
                probe("availability"),
            ),
            environment={
                "platform": "darwin",
                "api_token": (
                    "must-not-be-stored"
                ),
            },
        )
