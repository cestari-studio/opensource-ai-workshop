# Mellea + Granite Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize the workshop-owned authority foundation: immutable upstream locks, Mellea discovery verification, capability catalog, desired settings, RBAC+ABAC authorization, Granite provider overlays, and a deterministic coverage gate.

**Architecture:** The workshop owns a small isolated Python tooling package under `tools/workshop/`; it reads pinned upstream metadata and versioned YAML/JSON desired state but does not modify Mellea. Generated/runtime/provider certification is deliberately deferred. The first deliverable is a deterministic, testable authority layer that can answer: what exists, what is enabled, who may access it, and whether every active public capability is classified.

**Tech Stack:** Python 3.13, uv, pytest, PyYAML, jsonschema, argparse, Git/GitHub, YAML/JSON.

## Global Constraints

- Workshop upstream base is `IBM/opensource-ai-workshop` revision `1b1ddaa486ce40dc8b444da61d9b09b6643eed52`, tree `b5b02a0e92218ca4f2f1e40cd54056afc88afe59`.
- Mellea authority is `generative-computing/mellea` revision `853b04fe572b3f8d2947c56750c883aeae12ea0b` and remains pinned/read-only.
- No silent provider fallback.
- Granite 4.1 provider identity is explicit.
- Open WebUI is not required for core runtime operation.
- Public API does not imply public permission.
- Authorization is independent of Open WebUI persistence.
- Generated artifacts are not desired-state authority.
- Unsupported provider capabilities are explicitly classified.
- Execution enforcement gaps must be represented honestly.
- Every active capability has provenance.
- Do not add runtime inference dependencies to the repository root during this Foundation plan.
- All Foundation Python dependencies live under `tools/workshop/`.
- Tests run with `uv run --project tools/workshop python -m pytest ...`.

---

## File Structure Locked by This Plan

```text
authority/
└── mellea/
    ├── upstream.lock.json
    ├── capability-catalog.yaml
    └── coverage-policy.yaml

settings/
├── workshop.yaml
├── models.yaml
├── providers/
│   ├── ollama.yaml
│   ├── mlx.yaml
│   └── unsloth.yaml
└── authorization/
    ├── roles.yaml
    ├── levels.yaml
    ├── permissions.yaml
    └── policies.yaml

tools/workshop/
├── pyproject.toml
└── workshop_tools/
    ├── __init__.py
    ├── authority.py
    ├── catalog.py
    ├── settings.py
    ├── authorization.py
    ├── coverage.py
    └── cli.py

tests/workshop/
├── test_authority.py
├── test_catalog.py
├── test_settings.py
├── test_authorization.py
├── test_provider_overlays.py
├── test_coverage.py
└── test_cli.py
```

Responsibilities:

- `authority.py`: immutable repository lock parsing and checkout attestation.
- `catalog.py`: capability catalog loading, normalization, and validation.
- `settings.py`: deterministic settings merge/resolution.
- `authorization.py`: RBAC+ABAC evaluation over a resolved request context.
- `coverage.py`: source/catalog/settings/authorization consistency checks.
- `cli.py`: stable terminal surface named `workshopctl`.

---

### Task 1: Authority Locks and Isolated Tooling Environment

**Files:**
- Create: `tools/workshop/pyproject.toml`
- Create: `tools/workshop/workshop_tools/__init__.py`
- Create: `tools/workshop/workshop_tools/authority.py`
- Create: `authority/mellea/upstream.lock.json`
- Create: `tests/workshop/test_authority.py`

**Interfaces:**
- Produces: `RepositoryLock`, `load_repository_lock(path: Path) -> RepositoryLock`, `attest_checkout(lock: RepositoryLock, checkout: Path) -> CheckoutAttestation`.
- `CheckoutAttestation.ok` is true only when repository HEAD and tree match the lock exactly and the worktree is clean.

- [ ] **Step 1: Create the isolated tool project**

```toml
# tools/workshop/pyproject.toml
[project]
name = "opensource-ai-workshop-tools"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = [
  "jsonschema>=4.23,<5",
  "PyYAML>=6.0,<7",
]

[project.scripts]
workshopctl = "workshop_tools.cli:main"

[dependency-groups]
dev = [
  "pytest>=8.4,<9",
]

[tool.uv]
package = true
```

```python
# tools/workshop/workshop_tools/__init__.py
"""Authority and configuration tooling for the Open Source AI Workshop."""
```

Run:

```bash
uv sync --project tools/workshop --group dev
```

Expected: a tool-local environment is created and no repository-root `.venv` is required.

- [ ] **Step 2: Write the immutable Mellea lock**

```json
{
  "schemaVersion": "1.0.0",
  "repository": "generative-computing/mellea",
  "remote": "https://github.com/generative-computing/mellea.git",
  "revision": "853b04fe572b3f8d2947c56750c883aeae12ea0b",
  "mode": "read_only",
  "requiredCleanWorktree": true
}
```

Save as `authority/mellea/upstream.lock.json`.

- [ ] **Step 3: Write the failing authority tests**

```python
# tests/workshop/test_authority.py
from pathlib import Path
import subprocess

from workshop_tools.authority import attest_checkout, load_repository_lock


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def test_load_mellea_lock() -> None:
    lock = load_repository_lock(Path("authority/mellea/upstream.lock.json"))
    assert lock.repository == "generative-computing/mellea"
    assert lock.revision == "853b04fe572b3f8d2947c56750c883aeae12ea0b"
    assert lock.mode == "read_only"
    assert lock.required_clean_worktree is True


def test_attest_checkout_accepts_exact_clean_checkout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Workshop Test"], cwd=repo, check=True)
    (repo / "a.txt").write_text("a\n")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

    sha = git("rev-parse", "HEAD", cwd=repo)
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(
        '{"schemaVersion":"1.0.0","repository":"test/repo",'
        f'"remote":"local","revision":"{sha}","mode":"read_only",'
        '"requiredCleanWorktree":true}'
    )

    lock = load_repository_lock(lock_path)
    result = attest_checkout(lock, repo)
    assert result.ok is True
    assert result.actual_revision == sha
    assert result.clean is True


def test_attest_checkout_rejects_dirty_checkout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Workshop Test"], cwd=repo, check=True)
    (repo / "a.txt").write_text("a\n")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    sha = git("rev-parse", "HEAD", cwd=repo)
    (repo / "a.txt").write_text("dirty\n")

    lock_path = tmp_path / "lock.json"
    lock_path.write_text(
        '{"schemaVersion":"1.0.0","repository":"test/repo",'
        f'"remote":"local","revision":"{sha}","mode":"read_only",'
        '"requiredCleanWorktree":true}'
    )

    result = attest_checkout(load_repository_lock(lock_path), repo)
    assert result.ok is False
    assert result.clean is False
```

- [ ] **Step 4: Run the tests and verify RED**

Run:

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_authority.py -v
```

Expected: FAIL because `workshop_tools.authority` does not exist.

- [ ] **Step 5: Implement authority attestation**

```python
# tools/workshop/workshop_tools/authority.py
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class RepositoryLock:
    repository: str
    remote: str
    revision: str
    mode: str
    required_clean_worktree: bool


@dataclass(frozen=True)
class CheckoutAttestation:
    expected_revision: str
    actual_revision: str
    expected_tree: str
    actual_tree: str
    clean: bool
    ok: bool


def _git(checkout: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=checkout, text=True, stderr=subprocess.STDOUT
    ).strip()


def load_repository_lock(path: Path) -> RepositoryLock:
    data = json.loads(path.read_text())
    return RepositoryLock(
        repository=str(data["repository"]),
        remote=str(data["remote"]),
        revision=str(data["revision"]),
        mode=str(data["mode"]),
        required_clean_worktree=bool(data.get("requiredCleanWorktree", True)),
    )


def attest_checkout(lock: RepositoryLock, checkout: Path) -> CheckoutAttestation:
    expected_revision = lock.revision
    actual_revision = _git(checkout, "rev-parse", "HEAD")
    expected_tree = _git(checkout, "rev-parse", f"{expected_revision}^{{tree}}")
    actual_tree = _git(checkout, "rev-parse", "HEAD^{tree}")
    clean = _git(checkout, "status", "--porcelain") == ""
    ok = (
        actual_revision == expected_revision
        and actual_tree == expected_tree
        and (clean or not lock.required_clean_worktree)
    )
    return CheckoutAttestation(
        expected_revision=expected_revision,
        actual_revision=actual_revision,
        expected_tree=expected_tree,
        actual_tree=actual_tree,
        clean=clean,
        ok=ok,
    )
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_authority.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add tools/workshop authority/mellea/upstream.lock.json tests/workshop/test_authority.py
git diff --cached --check
git commit -m "feat(authority): add immutable Mellea checkout attestation"
```

---

### Task 2: Deterministic Mellea Discovery Verifier

**Files:**
- Create: `tools/workshop/workshop_tools/catalog.py`
- Create: `tests/workshop/test_catalog.py`
- Create after running verifier: `authority/mellea/source-manifest.json`

**Interfaces:**
- Consumes: an immutable Mellea checkout path.
- Produces: `SourceEntry(path, kind, sha256)` and `discover_source(checkout: Path) -> list[SourceEntry]`.
- Paths are deterministic, POSIX-formatted, sorted, and exclude `.git`, virtualenvs, caches, binary model weights, and generated Python caches.

- [ ] **Step 1: Write failing deterministic discovery tests**

```python
# tests/workshop/test_catalog.py
from pathlib import Path

from workshop_tools.catalog import discover_source


def test_discovery_is_sorted_and_classifies_files(tmp_path: Path) -> None:
    (tmp_path / "mellea").mkdir()
    (tmp_path / "docs" / "examples").mkdir(parents=True)
    (tmp_path / "test").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "mellea" / "session.py").write_text("x = 1\n")
    (tmp_path / "docs" / "guide.md").write_text("# guide\n")
    (tmp_path / "docs" / "examples" / "demo.py").write_text("print('x')\n")
    (tmp_path / "test" / "test_session.py").write_text("def test_x(): pass\n")
    (tmp_path / ".git" / "config").write_text("ignored\n")

    rows = discover_source(tmp_path)
    assert [row.path for row in rows] == sorted(row.path for row in rows)
    assert [row.kind for row in rows] == ["documentation", "example", "source", "test"]
    assert all(len(row.sha256) == 64 for row in rows)
    assert not any(row.path.startswith(".git/") for row in rows)


def test_discovery_hash_changes_when_content_changes(tmp_path: Path) -> None:
    (tmp_path / "mellea").mkdir()
    path = tmp_path / "mellea" / "a.py"
    path.write_text("a\n")
    first = discover_source(tmp_path)[0].sha256
    path.write_text("b\n")
    second = discover_source(tmp_path)[0].sha256
    assert first != second
```

- [ ] **Step 2: Verify RED**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_catalog.py -v
```

Expected: FAIL because discovery is missing.

- [ ] **Step 3: Implement deterministic discovery**

```python
# tools/workshop/workshop_tools/catalog.py
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path


EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
EXCLUDED_SUFFIXES = {".gguf", ".safetensors", ".bin", ".pt", ".pth", ".pyc"}


@dataclass(frozen=True)
class SourceEntry:
    path: str
    kind: str
    sha256: str


def classify(path: str) -> str:
    if path.startswith("docs/examples/"):
        return "example"
    if path.startswith("docs/"):
        return "documentation"
    if path.startswith("test/") or path.startswith("tests/"):
        return "test"
    if path.startswith("mellea/") or path.startswith("cli/"):
        return "source"
    return "engineering"


def discover_source(checkout: Path) -> list[SourceEntry]:
    rows: list[SourceEntry] = []
    for path in checkout.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(checkout)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        rel_posix = rel.as_posix()
        rows.append(
            SourceEntry(
                path=rel_posix,
                kind=classify(rel_posix),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return sorted(rows, key=lambda row: row.path)


def write_source_manifest(entries: list[SourceEntry], output: Path, revision: str) -> None:
    payload = {
        "schemaVersion": "1.0.0",
        "revision": revision,
        "entries": [asdict(entry) for entry in entries],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
```

- [ ] **Step 4: Verify GREEN**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_catalog.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Generate the pinned source manifest from the actual local Mellea checkout**

Expected local checkout for execution:

```bash
MELLEA_CHECKOUT="/Users/cestari/Developer/mainframe/upstreams/generative-computing/mellea"
```

Run:

```bash
uv run --project tools/workshop python - <<'PY'
from pathlib import Path
from workshop_tools.authority import attest_checkout, load_repository_lock
from workshop_tools.catalog import discover_source, write_source_manifest

lock = load_repository_lock(Path("authority/mellea/upstream.lock.json"))
checkout = Path("/Users/cestari/Developer/mainframe/upstreams/generative-computing/mellea")
attestation = attest_checkout(lock, checkout)
if not attestation.ok:
    raise SystemExit(f"MELLEA_ATTESTATION=FAIL {attestation}")
entries = discover_source(checkout)
write_source_manifest(entries, Path("authority/mellea/source-manifest.json"), lock.revision)
print(f"MELLEA_SOURCE_FILES={len(entries)}")
print("MELLEA_DISCOVERY=PASS")
PY
```

Expected: `MELLEA_DISCOVERY=PASS`.

- [ ] **Step 6: Commit**

```bash
git add tools/workshop/workshop_tools/catalog.py tests/workshop/test_catalog.py authority/mellea/source-manifest.json
git diff --cached --check
git commit -m "feat(authority): add deterministic Mellea source discovery"
```

---

### Task 3: Capability Catalog Schema and Seed Catalog

**Files:**
- Modify: `tools/workshop/workshop_tools/catalog.py`
- Create: `authority/mellea/capability-catalog.yaml`
- Create: `tests/workshop/test_catalog.py` additional tests

**Interfaces:**
- Produces: `Capability`, `load_capability_catalog(path: Path) -> list[Capability]`, `validate_capability_catalog(capabilities, source_paths) -> list[str]`.
- Every capability has `id`, `domain`, `status`, source paths, surfaces, evidence flags, and authorization metadata for public surfaces.

- [ ] **Step 1: Add failing validation tests**

Append:

```python
from workshop_tools.catalog import load_capability_catalog, validate_capability_catalog


def test_public_capability_requires_authorization(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.yaml"
    catalog.write_text(
        """
capabilities:
  - id: generation.instruct
    domain: generation
    status: WORKSHOP_NATIVE
    source_paths: [mellea/stdlib/session.py]
    surfaces: [python, api]
    evidence: {source: true, documented: true, exampled: true, tested: true}
"""
    )
    caps = load_capability_catalog(catalog)
    errors = validate_capability_catalog(caps, {"mellea/stdlib/session.py"})
    assert "generation.instruct: public surface requires authorization.permission" in errors


def test_catalog_rejects_unknown_source_path(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.yaml"
    catalog.write_text(
        """
capabilities:
  - id: generation.instruct
    domain: generation
    status: WORKSHOP_NATIVE
    source_paths: [missing.py]
    surfaces: [python]
    evidence: {source: true, documented: false, exampled: false, tested: false}
"""
    )
    errors = validate_capability_catalog(load_capability_catalog(catalog), set())
    assert "generation.instruct: unknown source path missing.py" in errors
```

- [ ] **Step 2: Verify RED**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_catalog.py -v
```

- [ ] **Step 3: Implement catalog parsing and validation**

Add to `catalog.py`:

```python
from typing import Any
import yaml


@dataclass(frozen=True)
class Capability:
    id: str
    domain: str
    status: str
    source_paths: tuple[str, ...]
    surfaces: tuple[str, ...]
    evidence: dict[str, bool]
    authorization_permission: str | None


def load_capability_catalog(path: Path) -> list[Capability]:
    raw: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    result: list[Capability] = []
    for row in raw.get("capabilities", []):
        authorization = row.get("authorization") or {}
        result.append(
            Capability(
                id=str(row["id"]),
                domain=str(row["domain"]),
                status=str(row["status"]),
                source_paths=tuple(str(x) for x in row.get("source_paths", [])),
                surfaces=tuple(str(x) for x in row.get("surfaces", [])),
                evidence={str(k): bool(v) for k, v in (row.get("evidence") or {}).items()},
                authorization_permission=authorization.get("permission"),
            )
        )
    return result


def validate_capability_catalog(
    capabilities: list[Capability], source_paths: set[str]
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    public_surfaces = {"api", "cli", "computer", "openwebui"}
    for cap in capabilities:
        if cap.id in seen:
            errors.append(f"{cap.id}: duplicate capability id")
        seen.add(cap.id)
        for path in cap.source_paths:
            if path not in source_paths:
                errors.append(f"{cap.id}: unknown source path {path}")
        if public_surfaces.intersection(cap.surfaces) and not cap.authorization_permission:
            errors.append(f"{cap.id}: public surface requires authorization.permission")
    return errors
```

- [ ] **Step 4: Create the seed capability catalog**

Create `authority/mellea/capability-catalog.yaml` with the initial top-level capabilities, each linked to verified paths in `source-manifest.json`. Minimum IDs for this Foundation slice:

```yaml
schemaVersion: 1.0.0
melleaRevision: 853b04fe572b3f8d2947c56750c883aeae12ea0b
capabilities:
  - id: generation.instruct
    domain: generation
    status: WORKSHOP_ADAPTED
    source_paths:
      - mellea/stdlib/session.py
    surfaces: [python, api, cli, computer, openwebui]
    authorization:
      permission: generation.invoke
    evidence:
      source: true
      documented: true
      exampled: true
      tested: true

  - id: generation.chat
    domain: generation
    status: WORKSHOP_ADAPTED
    source_paths:
      - mellea/stdlib/session.py
    surfaces: [python, api, cli, computer, openwebui]
    authorization:
      permission: generation.invoke
    evidence:
      source: true
      documented: true
      exampled: true
      tested: true

  - id: generation.generative_stub
    domain: codegen
    status: WORKSHOP_ADAPTED
    source_paths:
      - mellea/stdlib/components/genstub.py
    surfaces: [python, cli, computer]
    authorization:
      permission: generation.codegen
    evidence:
      source: true
      documented: true
      exampled: true
      tested: true

  - id: documents.rich_document
    domain: documents
    status: WORKSHOP_ADAPTED
    source_paths:
      - mellea/stdlib/components/docs/richdocument.py
    surfaces: [python, cli, computer, openwebui]
    authorization:
      permission: documents.process
    evidence:
      source: true
      documented: true
      exampled: true
      tested: true

  - id: tools.mcp
    domain: tools
    status: WORKSHOP_ADAPTED
    source_paths:
      - mellea/stdlib/tools/mcp.py
    surfaces: [python, api, cli, computer, openwebui]
    authorization:
      permission: tools.mcp.invoke
    evidence:
      source: true
      documented: true
      exampled: true
      tested: true
```

Do not guess file paths. Before writing the final catalog, derive exact paths from `authority/mellea/source-manifest.json`.

- [ ] **Step 5: Verify GREEN**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_catalog.py -v
```

- [ ] **Step 6: Commit**

```bash
git add authority/mellea/capability-catalog.yaml tools/workshop/workshop_tools/catalog.py tests/workshop/test_catalog.py
git diff --cached --check
git commit -m "feat(authority): add Mellea capability catalog contract"
```

---

### Task 4: Desired Settings and Deterministic Inheritance

**Files:**
- Create: `tools/workshop/workshop_tools/settings.py`
- Create: `settings/workshop.yaml`
- Create: `settings/models.yaml`
- Create: `tests/workshop/test_settings.py`

**Interfaces:**
- Produces: `deep_merge(base: dict, override: dict) -> dict`, `resolve_settings(global_defaults, tenant, workspace, role_level, user) -> dict`.
- Merge precedence is exactly global -> tenant -> workspace -> role/level -> user.
- Lists replace; dictionaries merge recursively; scalar values replace.

- [ ] **Step 1: Write failing settings tests**

```python
# tests/workshop/test_settings.py
from workshop_tools.settings import deep_merge, resolve_settings


def test_deep_merge_merges_maps_and_replaces_lists() -> None:
    result = deep_merge(
        {"model": {"provider": "mlx", "options": {"temperature": 0.2}}, "tools": ["a"]},
        {"model": {"options": {"temperature": 0.7}}, "tools": ["b"]},
    )
    assert result == {
        "model": {"provider": "mlx", "options": {"temperature": 0.7}},
        "tools": ["b"],
    }


def test_resolve_settings_uses_canonical_precedence() -> None:
    result = resolve_settings(
        {"x": 0, "nested": {"a": "global"}},
        {"x": 1},
        {"x": 2},
        {"x": 3},
        {"x": 4, "nested": {"b": "user"}},
    )
    assert result["x"] == 4
    assert result["nested"] == {"a": "global", "b": "user"}
```

- [ ] **Step 2: Verify RED**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_settings.py -v
```

- [ ] **Step 3: Implement deterministic merge**

```python
# tools/workshop/workshop_tools/settings.py
from __future__ import annotations

from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def resolve_settings(
    global_defaults: dict[str, Any],
    tenant: dict[str, Any],
    workspace: dict[str, Any],
    role_level: dict[str, Any],
    user: dict[str, Any],
) -> dict[str, Any]:
    result = global_defaults
    for layer in (tenant, workspace, role_level, user):
        result = deep_merge(result, layer)
    return result
```

- [ ] **Step 4: Create baseline desired-state settings**

`settings/workshop.yaml`:

```yaml
schemaVersion: 1.0.0
runtimeFirst: true
openWebUIRequiredForCore: false
providerFallback:
  enabled: false
authorization:
  mode: rbac_abac
  inheritance: [global, tenant, workspace, role_level, user]
```

`settings/models.yaml`:

```yaml
schemaVersion: 1.0.0
models:
  granite.core:
    family: ibm-granite
    logicalModel: granite-4.1-3b
    contextLength: 131072
    providers:
      - granite.ollama
      - granite.mlx
      - granite.unsloth
```

- [ ] **Step 5: Verify GREEN and commit**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_settings.py -v
git add tools/workshop/workshop_tools/settings.py settings/workshop.yaml settings/models.yaml tests/workshop/test_settings.py
git diff --cached --check
git commit -m "feat(settings): add deterministic workshop settings inheritance"
```

---

### Task 5: RBAC + ABAC Authorization Contract

**Files:**
- Create: `tools/workshop/workshop_tools/authorization.py`
- Create: `settings/authorization/roles.yaml`
- Create: `settings/authorization/levels.yaml`
- Create: `settings/authorization/permissions.yaml`
- Create: `settings/authorization/policies.yaml`
- Create: `tests/workshop/test_authorization.py`

**Interfaces:**
- Produces: `AccessContext`, `Policy`, `Decision`, `authorize(context, permission, policies) -> Decision`.
- Default is deny.
- A matching explicit deny wins over allow.
- Tenant/workspace mismatch denies.
- Required level is ordinal and enforced.

- [ ] **Step 1: Write failing authorization tests**

```python
# tests/workshop/test_authorization.py
from workshop_tools.authorization import AccessContext, Policy, authorize


def ctx(**overrides):
    base = dict(
        tenant_id="tenant-master",
        workspace_id="workspace-dev",
        user_id="user-1",
        role="developer",
        level=30,
    )
    base.update(overrides)
    return AccessContext(**base)


def test_default_deny() -> None:
    decision = authorize(ctx(), "generation.invoke", [])
    assert decision.allowed is False
    assert decision.reason == "default_deny"


def test_matching_allow() -> None:
    policies = [Policy(effect="allow", permission="generation.invoke", roles=("developer",), minimum_level=20)]
    assert authorize(ctx(), "generation.invoke", policies).allowed is True


def test_deny_wins() -> None:
    policies = [
        Policy(effect="allow", permission="tools.shell.execute", roles=("developer",), minimum_level=20),
        Policy(effect="deny", permission="tools.shell.execute", roles=("developer",), minimum_level=0),
    ]
    decision = authorize(ctx(), "tools.shell.execute", policies)
    assert decision.allowed is False
    assert decision.reason == "explicit_deny"


def test_minimum_level_is_enforced() -> None:
    policies = [Policy(effect="allow", permission="admin.settings.write", roles=("workspace_admin",), minimum_level=80)]
    decision = authorize(ctx(role="workspace_admin", level=50), "admin.settings.write", policies)
    assert decision.allowed is False
```

- [ ] **Step 2: Verify RED**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_authorization.py -v
```

- [ ] **Step 3: Implement authorization**

```python
# tools/workshop/workshop_tools/authorization.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AccessContext:
    tenant_id: str
    workspace_id: str
    user_id: str
    role: str
    level: int


@dataclass(frozen=True)
class Policy:
    effect: str
    permission: str
    roles: tuple[str, ...] = ()
    minimum_level: int = 0
    tenant_id: str | None = None
    workspace_id: str | None = None


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def _matches(context: AccessContext, permission: str, policy: Policy) -> bool:
    if policy.permission != permission:
        return False
    if policy.roles and context.role not in policy.roles:
        return False
    if context.level < policy.minimum_level:
        return False
    if policy.tenant_id is not None and context.tenant_id != policy.tenant_id:
        return False
    if policy.workspace_id is not None and context.workspace_id != policy.workspace_id:
        return False
    return True


def authorize(context: AccessContext, permission: str, policies: list[Policy]) -> Decision:
    matching = [policy for policy in policies if _matches(context, permission, policy)]
    if any(policy.effect == "deny" for policy in matching):
        return Decision(False, "explicit_deny")
    if any(policy.effect == "allow" for policy in matching):
        return Decision(True, "explicit_allow")
    return Decision(False, "default_deny")
```

- [ ] **Step 4: Create canonical role/level/permission settings**

`settings/authorization/levels.yaml`:

```yaml
schemaVersion: 1.0.0
levels:
  guest: 0
  member: 10
  practitioner: 20
  developer: 30
  senior_developer: 40
  workspace_admin: 80
  tenant_admin: 90
  operator: 100
```

`settings/authorization/roles.yaml`:

```yaml
schemaVersion: 1.0.0
roles:
  member:
    defaultLevel: member
  developer:
    defaultLevel: developer
  workspace_admin:
    defaultLevel: workspace_admin
  tenant_admin:
    defaultLevel: tenant_admin
  operator:
    defaultLevel: operator
```

`settings/authorization/permissions.yaml`:

```yaml
schemaVersion: 1.0.0
permissions:
  - generation.invoke
  - generation.codegen
  - documents.process
  - tools.mcp.invoke
  - tools.shell.execute
  - settings.read
  - settings.write
  - administration.global
```

`settings/authorization/policies.yaml`:

```yaml
schemaVersion: 1.0.0
policies:
  - effect: allow
    permission: generation.invoke
    roles: [member, developer, workspace_admin, tenant_admin, operator]
    minimumLevel: 10
  - effect: allow
    permission: generation.codegen
    roles: [developer, workspace_admin, tenant_admin, operator]
    minimumLevel: 30
  - effect: allow
    permission: documents.process
    roles: [developer, workspace_admin, tenant_admin, operator]
    minimumLevel: 30
  - effect: allow
    permission: tools.mcp.invoke
    roles: [developer, workspace_admin, tenant_admin, operator]
    minimumLevel: 30
  - effect: allow
    permission: tools.shell.execute
    roles: [developer, workspace_admin, tenant_admin, operator]
    minimumLevel: 30
  - effect: allow
    permission: settings.write
    roles: [workspace_admin, tenant_admin, operator]
    minimumLevel: 80
  - effect: allow
    permission: administration.global
    roles: [operator]
    minimumLevel: 100
```

- [ ] **Step 5: Verify GREEN and commit**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_authorization.py -v
git add tools/workshop/workshop_tools/authorization.py settings/authorization tests/workshop/test_authorization.py
git diff --cached --check
git commit -m "feat(auth): add workspace RBAC and ABAC authorization contract"
```

---

### Task 6: Granite 4.1 Provider Overlays

**Files:**
- Create: `settings/providers/ollama.yaml`
- Create: `settings/providers/mlx.yaml`
- Create: `settings/providers/unsloth.yaml`
- Create: `tests/workshop/test_provider_overlays.py`

**Interfaces:**
- Each provider file defines one stable profile ID and must identify Granite 4.1 explicitly.
- No provider may declare fallback.
- MLX and Unsloth are workshop overlays and do not mutate Mellea `ModelIdentifier`.

- [ ] **Step 1: Create provider settings**

`settings/providers/ollama.yaml`:

```yaml
schemaVersion: 1.0.0
profile: granite.ollama
provider: ollama
model:
  family: ibm-granite
  logical: granite-4.1-3b
  providerId: granite4.1:3b
protocol: native_mellea_ollama
fallback:
  enabled: false
certification:
  status: pending
```

`settings/providers/mlx.yaml`:

```yaml
schemaVersion: 1.0.0
profile: granite.mlx
provider: mlx-lm
model:
  family: ibm-granite
  logical: granite-4.1-3b
  providerId: ibm-granite/granite-4.1-3b
protocol: openai_compatible
endpoint: http://127.0.0.1:8080/v1
fallback:
  enabled: false
certification:
  status: pending
```

`settings/providers/unsloth.yaml`:

```yaml
schemaVersion: 1.0.0
profile: granite.unsloth
provider: unsloth-studio
model:
  family: ibm-granite
  logical: granite-4.1-3b
  providerId: unsloth/granite-4.1-3b-GGUF
protocol: openai_compatible
endpoint: http://127.0.0.1:8888/v1
fallback:
  enabled: false
certification:
  status: pending
```

- [ ] **Step 2: Write provider invariant tests**

```python
# tests/workshop/test_provider_overlays.py
from pathlib import Path
import yaml


def load(name: str) -> dict:
    return yaml.safe_load(Path(f"settings/providers/{name}.yaml").read_text())


def test_provider_profiles_are_unique_and_no_fallback() -> None:
    docs = [load("ollama"), load("mlx"), load("unsloth")]
    profiles = [doc["profile"] for doc in docs]
    assert len(profiles) == len(set(profiles))
    assert profiles == ["granite.ollama", "granite.mlx", "granite.unsloth"]
    assert all(doc["fallback"]["enabled"] is False for doc in docs)


def test_all_profiles_are_granite_4_1_3b() -> None:
    for name in ("ollama", "mlx", "unsloth"):
        doc = load(name)
        assert doc["model"]["family"] == "ibm-granite"
        assert doc["model"]["logical"] == "granite-4.1-3b"


def test_certification_starts_pending() -> None:
    for name in ("ollama", "mlx", "unsloth"):
        assert load(name)["certification"]["status"] == "pending"
```

- [ ] **Step 3: Run tests and commit**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_provider_overlays.py -v
git add settings/providers tests/workshop/test_provider_overlays.py
git diff --cached --check
git commit -m "feat(providers): define Granite 4.1 provider overlays"
```

---

### Task 7: Coverage Gate

**Files:**
- Create: `tools/workshop/workshop_tools/coverage.py`
- Create: `authority/mellea/coverage-policy.yaml`
- Create: `tests/workshop/test_coverage.py`

**Interfaces:**
- Produces `CoverageIssue(code, message)` and `check_coverage(capabilities, permissions, source_paths) -> list[CoverageIssue]`.
- Fails when a catalog source path is unknown, a public capability has no permission, or a permission referenced by a capability is not declared.

- [ ] **Step 1: Write failing coverage tests**

```python
# tests/workshop/test_coverage.py
from workshop_tools.catalog import Capability
from workshop_tools.coverage import check_coverage


def capability(permission: str | None = "generation.invoke") -> Capability:
    return Capability(
        id="generation.instruct",
        domain="generation",
        status="WORKSHOP_ADAPTED",
        source_paths=("mellea/stdlib/session.py",),
        surfaces=("api",),
        evidence={"source": True},
        authorization_permission=permission,
    )


def test_unknown_permission_fails_coverage() -> None:
    issues = check_coverage(
        [capability("generation.invoke")],
        declared_permissions={"other.permission"},
        source_paths={"mellea/stdlib/session.py"},
    )
    assert [issue.code for issue in issues] == ["UNKNOWN_PERMISSION"]


def test_valid_capability_passes_coverage() -> None:
    issues = check_coverage(
        [capability()],
        declared_permissions={"generation.invoke"},
        source_paths={"mellea/stdlib/session.py"},
    )
    assert issues == []
```

- [ ] **Step 2: Verify RED**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_coverage.py -v
```

- [ ] **Step 3: Implement coverage**

```python
# tools/workshop/workshop_tools/coverage.py
from __future__ import annotations

from dataclasses import dataclass

from .catalog import Capability


@dataclass(frozen=True)
class CoverageIssue:
    code: str
    message: str


def check_coverage(
    capabilities: list[Capability],
    declared_permissions: set[str],
    source_paths: set[str],
) -> list[CoverageIssue]:
    issues: list[CoverageIssue] = []
    public_surfaces = {"api", "cli", "computer", "openwebui"}
    for cap in capabilities:
        for path in cap.source_paths:
            if path not in source_paths:
                issues.append(CoverageIssue("UNKNOWN_SOURCE", f"{cap.id}: {path}"))
        if public_surfaces.intersection(cap.surfaces):
            if cap.authorization_permission is None:
                issues.append(CoverageIssue("MISSING_PERMISSION", cap.id))
            elif cap.authorization_permission not in declared_permissions:
                issues.append(
                    CoverageIssue(
                        "UNKNOWN_PERMISSION",
                        f"{cap.id}: {cap.authorization_permission}",
                    )
                )
    return issues
```

`authority/mellea/coverage-policy.yaml`:

```yaml
schemaVersion: 1.0.0
failOn:
  - UNKNOWN_SOURCE
  - MISSING_PERMISSION
  - UNKNOWN_PERMISSION
publicSurfaces:
  - api
  - cli
  - computer
  - openwebui
```

- [ ] **Step 4: Verify GREEN and commit**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_coverage.py -v
git add tools/workshop/workshop_tools/coverage.py authority/mellea/coverage-policy.yaml tests/workshop/test_coverage.py
git diff --cached --check
git commit -m "feat(authority): enforce capability coverage invariants"
```

---

### Task 8: `workshopctl` Foundation CLI and End-to-End Gate

**Files:**
- Create: `tools/workshop/workshop_tools/cli.py`
- Create: `tests/workshop/test_cli.py`

**Interfaces:**
- CLI commands:
  - `workshopctl authority attest --checkout PATH`
  - `workshopctl coverage check`
  - `workshopctl settings resolve FILE...`
- Exit code 0 means gate passed; non-zero means failure.

- [ ] **Step 1: Write failing CLI tests**

```python
# tests/workshop/test_cli.py
from pathlib import Path
import subprocess
import sys


def test_coverage_check_passes_repository_state() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "workshop_tools.cli", "coverage", "check"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "COVERAGE=PASS" in result.stdout
```

- [ ] **Step 2: Verify RED**

```bash
uv run --project tools/workshop python -m pytest tests/workshop/test_cli.py -v
```

- [ ] **Step 3: Implement CLI**

```python
# tools/workshop/workshop_tools/cli.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

from .authority import attest_checkout, load_repository_lock
from .catalog import load_capability_catalog
from .coverage import check_coverage
from .settings import deep_merge


def _permissions() -> set[str]:
    data = yaml.safe_load(Path("settings/authorization/permissions.yaml").read_text())
    return {str(x) for x in data["permissions"]}


def _source_paths() -> set[str]:
    data = json.loads(Path("authority/mellea/source-manifest.json").read_text())
    return {str(row["path"]) for row in data["entries"]}


def coverage_check() -> int:
    caps = load_capability_catalog(Path("authority/mellea/capability-catalog.yaml"))
    issues = check_coverage(caps, _permissions(), _source_paths())
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.message}")
        print("COVERAGE=FAIL")
        return 1
    print("COVERAGE=PASS")
    return 0


def authority_attest(checkout: str) -> int:
    lock = load_repository_lock(Path("authority/mellea/upstream.lock.json"))
    result = attest_checkout(lock, Path(checkout))
    print(json.dumps(result.__dict__, indent=2, sort_keys=True))
    print("MELLEA_ATTESTATION=PASS" if result.ok else "MELLEA_ATTESTATION=FAIL")
    return 0 if result.ok else 1


def settings_resolve(files: list[str]) -> int:
    resolved: dict = {}
    for file in files:
        layer = yaml.safe_load(Path(file).read_text()) or {}
        resolved = deep_merge(resolved, layer)
    print(yaml.safe_dump(resolved, sort_keys=True), end="")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="workshopctl")
    sub = root.add_subparsers(dest="domain", required=True)

    authority = sub.add_parser("authority")
    authority_sub = authority.add_subparsers(dest="action", required=True)
    attest = authority_sub.add_parser("attest")
    attest.add_argument("--checkout", required=True)

    coverage = sub.add_parser("coverage")
    coverage_sub = coverage.add_subparsers(dest="action", required=True)
    coverage_sub.add_parser("check")

    settings = sub.add_parser("settings")
    settings_sub = settings.add_subparsers(dest="action", required=True)
    resolve = settings_sub.add_parser("resolve")
    resolve.add_argument("files", nargs="+")
    return root


def main() -> None:
    args = parser().parse_args()
    if args.domain == "authority" and args.action == "attest":
        raise SystemExit(authority_attest(args.checkout))
    if args.domain == "coverage" and args.action == "check":
        raise SystemExit(coverage_check())
    if args.domain == "settings" and args.action == "resolve":
        raise SystemExit(settings_resolve(args.files))
    raise SystemExit(2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run full Foundation suite**

```bash
uv run --project tools/workshop python -m pytest tests/workshop -v
```

Expected: all Foundation tests pass.

- [ ] **Step 5: Run real upstream and coverage gates**

```bash
uv run --project tools/workshop workshopctl authority attest \
  --checkout /Users/cestari/Developer/mainframe/upstreams/generative-computing/mellea

uv run --project tools/workshop workshopctl coverage check
```

Expected:

```text
MELLEA_ATTESTATION=PASS
COVERAGE=PASS
```

- [ ] **Step 6: Verify no generated/runtime materialization was accidentally introduced**

```bash
test ! -d generated || {
  echo "FAIL: generated/ must not be materialized during Foundation"
  exit 1
}

git diff --check
git status --short
```

- [ ] **Step 7: Commit**

```bash
git add tools/workshop/workshop_tools/cli.py tests/workshop/test_cli.py
git diff --cached --check
git commit -m "feat(cli): add workshop authority and coverage gates"
```

---

## Foundation Completion Gate

Run exactly:

```bash
set -euo pipefail

uv sync --project tools/workshop --group dev
uv run --project tools/workshop python -m pytest tests/workshop -v

uv run --project tools/workshop workshopctl authority attest \
  --checkout /Users/cestari/Developer/mainframe/upstreams/generative-computing/mellea

uv run --project tools/workshop workshopctl coverage check

git diff --check
git status --short --branch
```

Foundation is complete only when the output includes:

```text
MELLEA_ATTESTATION=PASS
COVERAGE=PASS
```

and all `tests/workshop` tests pass.

## Follow-on Plans

This Foundation plan intentionally does not implement runtime inference or Open WebUI. After its completion, create separate independently testable plans in this order:

1. `Mellea + Granite Provider Certification` — Ollama, MLX, Unsloth and Mellea capability matrix.
2. `Workshop Document + Code Generator` — generation profiles, IVR, GenStub, Document/RichDocument, receipts.
3. `Tools + Knowledge Plane` — native tools, execution policy, MCP, MCPO, OIKB, FAISS/RAG.
4. `Development + Experience Plane` — CLI workflows, Computer/Open Terminal, `m serve`, Open WebUI Web/Desktop.
5. `Persistence Migration` — SQLite compatibility adapter followed by PostgreSQL implementation while preserving public domain identifiers.

## Self-Review Results

- Spec coverage for Foundation: authority, catalog, settings, authorization, provider overlays, and coverage are each assigned a task.
- Runtime provider certification is explicitly deferred to its own plan because it is independently testable and hardware/service dependent.
- No `TODO`, `TBD`, `FIXME`, or placeholder implementation steps are intentionally present.
- Shared interface names are consistent across tasks: `RepositoryLock`, `Capability`, `deep_merge`, `AccessContext`, `Policy`, `check_coverage`, and `workshopctl`.
