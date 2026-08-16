from pathlib import Path

from workshop_tools.catalog import discover_source


def test_discovery_is_sorted_and_classifies_files(
    tmp_path: Path,
) -> None:
    (tmp_path / "mellea").mkdir()
    (tmp_path / "docs" / "examples").mkdir(parents=True)
    (tmp_path / "test").mkdir()
    (tmp_path / ".git").mkdir()

    (tmp_path / "mellea" / "session.py").write_text(
        "x = 1\n"
    )
    (tmp_path / "docs" / "guide.md").write_text(
        "# guide\n"
    )
    (
        tmp_path
        / "docs"
        / "examples"
        / "demo.py"
    ).write_text(
        "print('x')\n"
    )
    (
        tmp_path
        / "test"
        / "test_session.py"
    ).write_text(
        "def test_x(): pass\n"
    )
    (
        tmp_path
        / ".git"
        / "config"
    ).write_text(
        "ignored\n"
    )

    rows = discover_source(tmp_path)

    assert [row.path for row in rows] == sorted(
        row.path for row in rows
    )

    assert [row.kind for row in rows] == [
        "example",
        "documentation",
        "source",
        "test",
    ]

    assert all(
        len(row.sha256) == 64
        for row in rows
    )

    assert not any(
        row.path.startswith(".git/")
        for row in rows
    )


def test_discovery_hash_changes_when_content_changes(
    tmp_path: Path,
) -> None:
    (tmp_path / "mellea").mkdir()

    path = tmp_path / "mellea" / "a.py"
    path.write_text("a\n")

    first = discover_source(tmp_path)[0].sha256

    path.write_text("b\n")

    second = discover_source(tmp_path)[0].sha256

    assert first != second


def test_discovery_excludes_generated_and_model_artifacts(
    tmp_path: Path,
) -> None:
    (tmp_path / "mellea").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "__pycache__").mkdir()

    (tmp_path / "mellea" / "valid.py").write_text(
        "x = 1\n"
    )
    (tmp_path / ".venv" / "ignored.py").write_text(
        "ignored\n"
    )
    (
        tmp_path
        / "__pycache__"
        / "ignored.pyc"
    ).write_bytes(b"ignored")

    (tmp_path / "weights.gguf").write_bytes(
        b"model"
    )
    (tmp_path / "weights.safetensors").write_bytes(
        b"model"
    )

    rows = discover_source(tmp_path)

    assert [row.path for row in rows] == [
        "mellea/valid.py"
    ]



def test_public_capability_requires_authorization(
    tmp_path: Path,
) -> None:
    from workshop_tools.catalog import (
        load_capability_catalog,
        validate_capability_catalog,
    )

    catalog = tmp_path / "catalog.yaml"

    catalog.write_text(
        """
capabilities:
  - id: generation.instruct
    domain: generation
    status: WORKSHOP_NATIVE
    source_paths:
      - mellea/stdlib/session.py
    surfaces:
      - python
      - api
    evidence:
      source: true
      documented: true
      exampled: true
      tested: true
"""
    )

    capabilities = load_capability_catalog(
        catalog
    )

    errors = validate_capability_catalog(
        capabilities,
        {"mellea/stdlib/session.py"},
    )

    assert (
        "generation.instruct: public surface "
        "requires authorization.permission"
        in errors
    )


def test_catalog_rejects_unknown_source_path(
    tmp_path: Path,
) -> None:
    from workshop_tools.catalog import (
        load_capability_catalog,
        validate_capability_catalog,
    )

    catalog = tmp_path / "catalog.yaml"

    catalog.write_text(
        """
capabilities:
  - id: generation.instruct
    domain: generation
    status: WORKSHOP_NATIVE
    source_paths:
      - missing.py
    surfaces:
      - python
    evidence:
      source: true
      documented: false
      exampled: false
      tested: false
"""
    )

    errors = validate_capability_catalog(
        load_capability_catalog(catalog),
        set(),
    )

    assert (
        "generation.instruct: "
        "unknown source path missing.py"
        in errors
    )


def test_seed_catalog_validates_against_real_source_manifest() -> None:
    import json

    from workshop_tools.catalog import (
        load_capability_catalog,
        validate_capability_catalog,
    )

    manifest = json.loads(
        Path(
            "authority/mellea/source-manifest.json"
        ).read_text()
    )

    source_paths = {
        row["path"]
        for row in manifest["entries"]
    }

    capabilities = load_capability_catalog(
        Path(
            "authority/mellea/"
            "capability-catalog.yaml"
        )
    )

    errors = validate_capability_catalog(
        capabilities,
        source_paths,
    )

    assert errors == []

    ids = {
        capability.id
        for capability in capabilities
    }

    assert {
        "generation.instruct",
        "generation.chat",
        "generation.generative_stub",
        "documents.rich_document",
        "tools.mcp",
    }.issubset(ids)
