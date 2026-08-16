import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = (
    Path(__file__).resolve().parents[2]
)


def run_cli(
    *args: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "workshop_tools.cli",
            *args,
        ],
        cwd=(
            cwd
            if cwd is not None
            else REPOSITORY_ROOT
        ),
        text=True,
        capture_output=True,
    )


def test_help_exposes_provider_domain() -> None:
    result = run_cli(
        "--help"
    )

    assert result.returncode == 0
    assert "provider" in result.stdout


def test_provider_list_is_deterministic() -> None:
    result = run_cli(
        "provider",
        "list",
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )

    data = json.loads(
        result.stdout
    )

    assert [
        row["profile"]
        for row in data
    ] == [
        "granite.mlx",
        "granite.ollama",
        "granite.unsloth",
    ]

    assert all(
        row["fallbackEnabled"] is False
        for row in data
    )

    assert all(
        row["certificationStatus"]
        == "pending"
        for row in data
    )


def test_provider_inspect_returns_exact_mlx_profile() -> None:
    result = run_cli(
        "provider",
        "inspect",
        "granite.mlx",
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )

    data = json.loads(
        result.stdout
    )

    assert data == {
        "certificationStatus": "pending",
        "endpoint": (
            "http://127.0.0.1:8080/v1"
        ),
        "fallbackEnabled": False,
        "model": {
            "logical": "granite-4.1-3b",
            "providerId": (
                "ibm-granite/granite-4.1-3b"
            ),
        },
        "profile": "granite.mlx",
        "protocol": "openai_compatible",
        "provider": "mlx-lm",
        "providerCertified": False,
        "schemaVersion": "1.0.0",
    }


def test_provider_inspect_preserves_null_endpoint() -> None:
    result = run_cli(
        "provider",
        "inspect",
        "granite.ollama",
    )

    assert result.returncode == 0, (
        result.stdout
        + result.stderr
    )

    data = json.loads(
        result.stdout
    )

    assert (
        data["profile"]
        == "granite.ollama"
    )

    assert (
        data["model"]["providerId"]
        == "granite4.1:3b"
    )

    assert data["endpoint"] is None
    assert data["fallbackEnabled"] is False


def test_provider_inspect_unknown_profile_is_nonzero() -> None:
    result = run_cli(
        "provider",
        "inspect",
        "granite.missing",
    )

    assert result.returncode != 0

    combined = (
        result.stdout
        + result.stderr
    )

    assert (
        "unknown provider profile"
        in combined
    )
