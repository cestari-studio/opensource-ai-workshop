from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

from .authority import (
    attest_checkout,
    load_repository_lock,
)
from .catalog import (
    load_capability_catalog,
)
from .coverage import (
    check_coverage,
)
from .settings import (
    deep_merge,
)
from .providers import (
    ProviderProfile,
    get_provider_profile,
    load_provider_registry,
)


def repository_root() -> Path:
    configured = os.environ.get(
        "WORKSHOP_ROOT"
    )

    if configured:
        root = Path(
            configured
        ).expanduser().resolve()

        if root.is_dir():
            return root

        raise RuntimeError(
            "WORKSHOP_ROOT is not "
            f"a directory: {root}"
        )

    here = Path(
        __file__
    ).resolve()

    for parent in here.parents:
        if (
            parent
            / "authority"
            / "mellea"
            / "upstream.lock.json"
        ).is_file() and (
            parent
            / "settings"
            / "workshop.yaml"
        ).is_file():
            return parent

    raise RuntimeError(
        "unable to locate workshop "
        "repository root; set "
        "WORKSHOP_ROOT"
    )


def _permissions(
    root: Path,
) -> set[str]:
    path = (
        root
        / "settings"
        / "authorization"
        / "permissions.yaml"
    )

    data = (
        yaml.safe_load(
            path.read_text()
        )
        or {}
    )

    permissions = data.get(
        "permissions",
        {}
    )

    if isinstance(
        permissions,
        dict,
    ):
        return {
            str(value)
            for value in permissions
        }

    return {
        str(value)
        for value in permissions
    }


def _source_paths(
    root: Path,
) -> set[str]:
    path = (
        root
        / "authority"
        / "mellea"
        / "source-manifest.json"
    )

    data = json.loads(
        path.read_text()
    )

    return {
        str(row["path"])
        for row in data["entries"]
    }


def coverage_check() -> int:
    root = repository_root()

    capabilities = (
        load_capability_catalog(
            root
            / "authority"
            / "mellea"
            / "capability-catalog.yaml"
        )
    )

    permissions = _permissions(
        root
    )

    source_paths = _source_paths(
        root
    )

    issues = check_coverage(
        capabilities,
        permissions,
        source_paths,
    )

    print(
        "COVERAGE_SOURCE_PATHS="
        f"{len(source_paths)}"
    )

    print(
        "COVERAGE_CAPABILITIES="
        f"{len(capabilities)}"
    )

    print(
        "COVERAGE_PERMISSIONS="
        f"{len(permissions)}"
    )

    if issues:
        for issue in issues:
            print(
                f"{issue.code}: "
                f"{issue.message}"
            )

        print("COVERAGE=FAIL")
        return 1

    print("COVERAGE=PASS")
    return 0


def authority_attest(
    checkout: str,
) -> int:
    root = repository_root()

    lock = load_repository_lock(
        root
        / "authority"
        / "mellea"
        / "upstream.lock.json"
    )

    checkout_path = (
        Path(checkout)
        .expanduser()
        .resolve()
    )

    try:
        result = attest_checkout(
            lock,
            checkout_path,
        )
    except (
        FileNotFoundError,
        NotADirectoryError,
        subprocess.CalledProcessError,
    ) as exc:
        print(
            json.dumps(
                {
                    "checkout": (
                        str(
                            checkout_path
                        )
                    ),
                    "error": str(exc),
                    "ok": False,
                },
                indent=2,
                sort_keys=True,
            )
        )

        print(
            "MELLEA_ATTESTATION=FAIL"
        )

        return 1

    print(
        json.dumps(
            result.__dict__,
            indent=2,
            sort_keys=True,
        )
    )

    if result.ok:
        print(
            "MELLEA_ATTESTATION=PASS"
        )

        return 0

    print(
        "MELLEA_ATTESTATION=FAIL"
    )

    return 1


def settings_resolve(
    files: list[str],
) -> int:
    resolved: dict = {}

    for filename in files:
        path = (
            Path(filename)
            .expanduser()
            .resolve()
        )

        layer = (
            yaml.safe_load(
                path.read_text()
            )
            or {}
        )

        if not isinstance(
            layer,
            dict,
        ):
            raise ValueError(
                "settings layer must "
                f"be a mapping: {path}"
            )

        resolved = deep_merge(
            resolved,
            layer,
        )

    print(
        yaml.safe_dump(
            resolved,
            sort_keys=True,
        ),
        end="",
    )

    return 0


def _provider_payload(
    profile: ProviderProfile,
) -> dict:
    return {
        "certificationStatus": (
            profile.certification_status
        ),
        "endpoint": profile.endpoint,
        "fallbackEnabled": (
            profile.fallback_enabled
        ),
        "model": {
            "logical": (
                profile.model_logical
            ),
            "providerId": (
                profile.model_provider_id
            ),
        },
        "profile": profile.profile,
        "protocol": profile.protocol,
        "provider": profile.provider,
        "providerCertified": (
            profile.provider_certified
        ),
        "schemaVersion": (
            profile.schema_version
        ),
    }


def provider_list() -> int:
    registry = load_provider_registry(
        repository_root()
    )

    payload = [
        _provider_payload(
            profile
        )
        for profile in registry.values()
    ]

    print(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


def provider_inspect(
    profile_name: str,
) -> int:
    registry = load_provider_registry(
        repository_root()
    )

    try:
        profile = get_provider_profile(
            registry,
            profile_name,
        )
    except KeyError as exc:
        print(
            exc.args[0],
            file=sys.stderr,
        )

        return 1

    print(
        json.dumps(
            _provider_payload(
                profile
            ),
            indent=2,
            sort_keys=True,
        )
    )

    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="workshopctl",
        description=(
            "Open Source AI Workshop "
            "authority and settings CLI"
        ),
    )

    sub = root.add_subparsers(
        dest="domain",
        required=True,
    )

    authority = sub.add_parser(
        "authority"
    )

    authority_sub = (
        authority.add_subparsers(
            dest="action",
            required=True,
        )
    )

    attest = (
        authority_sub.add_parser(
            "attest"
        )
    )

    attest.add_argument(
        "--checkout",
        required=True,
    )

    coverage = sub.add_parser(
        "coverage"
    )

    coverage_sub = (
        coverage.add_subparsers(
            dest="action",
            required=True,
        )
    )

    coverage_sub.add_parser(
        "check"
    )

    settings = sub.add_parser(
        "settings"
    )

    settings_sub = (
        settings.add_subparsers(
            dest="action",
            required=True,
        )
    )

    resolve = (
        settings_sub.add_parser(
            "resolve"
        )
    )

    resolve.add_argument(
        "files",
        nargs="+",
    )

    provider = sub.add_parser(
        "provider"
    )

    provider_sub = (
        provider.add_subparsers(
            dest="action",
            required=True,
        )
    )

    provider_sub.add_parser(
        "list"
    )

    inspect = (
        provider_sub.add_parser(
            "inspect"
        )
    )

    inspect.add_argument(
        "profile"
    )

    return root


def main() -> None:
    args = parser().parse_args()

    if (
        args.domain == "authority"
        and args.action == "attest"
    ):
        raise SystemExit(
            authority_attest(
                args.checkout
            )
        )

    if (
        args.domain == "coverage"
        and args.action == "check"
    ):
        raise SystemExit(
            coverage_check()
        )

    if (
        args.domain == "settings"
        and args.action == "resolve"
    ):
        raise SystemExit(
            settings_resolve(
                args.files
            )
        )

    if (
        args.domain == "provider"
        and args.action == "list"
    ):
        raise SystemExit(
            provider_list()
        )

    if (
        args.domain == "provider"
        and args.action == "inspect"
    ):
        raise SystemExit(
            provider_inspect(
                args.profile
            )
        )

    raise SystemExit(2)


if __name__ == "__main__":
    main()
