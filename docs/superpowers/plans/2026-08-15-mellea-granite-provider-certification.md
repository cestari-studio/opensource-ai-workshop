# Mellea + Granite Provider Certification Implementation Plan

Status: APPROVED-BOUNDARY
Date: 2026-08-15

## 1. Purpose

Certify IBM Granite 4.1 3B across the three explicit workshop provider
profiles established by the Foundation:

- granite.ollama
- granite.mlx
- granite.unsloth

Then certify Mellea behavior on top of those provider contracts.

This plan produces runtime evidence.

Configuration alone never implies certification.

## 2. Foundation dependency

Required Foundation revision:

    f66db76a305ebdc86bfcfbc118b2321fab307920

Required immutable Mellea revision:

    853b04fe572b3f8d2947c56750c883aeae12ea0b

The Mellea checkout remains read-only.

## 3. Provider identities

### granite.ollama

Provider:

    ollama

Model:

    granite4.1:3b

Mellea path:

    native OllamaBackend

Expected local provider API authority:

    http://127.0.0.1:11434

### granite.mlx

Provider:

    mlx-lm

Model:

    ibm-granite/granite-4.1-3b

Mellea path:

    OpenAI-compatible backend adapter

API:

    http://127.0.0.1:8080/v1

### granite.unsloth

Provider:

    unsloth-studio

Model family:

    unsloth/granite-4.1-3b-GGUF

Mellea path:

    OpenAI-compatible backend adapter

API:

    http://127.0.0.1:8888/v1

## 4. Non-negotiable runtime invariant

There is no provider fallback.

For example:

    requested = granite.mlx
    mlx unavailable
    result = FAIL / UNAVAILABLE

Never:

    granite.mlx
       ↓ failure
    granite.ollama

The same applies in the opposite direction and to Unsloth.

## 5. Evidence vocabulary

Every probe has exactly one status:

- PASS
- FAIL
- UNSUPPORTED
- NOT_APPLICABLE
- UNAVAILABLE

`UNSUPPORTED` means the provider was reachable and the capability was
determined not to exist or not to conform to the required contract.

`UNAVAILABLE` means the provider or required model was not reachable.

Neither status is silently converted to another provider.

## 6. Provider certification levels

Provider certification status is derived from probe evidence.

### certified

All required core and advanced probes pass.

### certified_with_limitations

All core probes pass, but one or more advanced capabilities are explicitly
UNSUPPORTED.

### failed

At least one required core probe fails.

### unavailable

The runtime/model cannot be reached and therefore cannot be certified.

## 7. Core provider probes

Every provider must execute, where applicable:

1. runtime availability
2. exact model discovery
3. exact model identity
4. basic generation
5. deterministic low-temperature generation
6. streaming
7. malformed-request behavior
8. unknown-model rejection
9. no-fallback verification

The provider cannot be certified if basic generation or identity fails.

## 8. Advanced provider probes

Each provider must explicitly test:

1. structured output
2. JSON output
3. tool declaration
4. tool calling
5. tool argument structure
6. finish reason
7. usage metadata where available
8. context/model metadata where available

Advanced probe failure may produce `certified_with_limitations` only when
the provider is otherwise usable and the unsupported capability is recorded
explicitly.

## 9. Mellea certification probes

After direct provider certification, test through Mellea.

Required baseline:

- backend construction
- session construction
- chat
- instruct
- async invocation
- streaming/lazy result handling
- model options
- user variables
- grounding context
- ICL examples

Generative-computing probes:

- requirements
- validation
- structured Pydantic output
- rejection sampling
- Instruct-Validate-Repair
- tool definition
- tool calling

A provider can pass its own API probes while failing Mellea compatibility.

These are separate evidence dimensions.

## 10. Certification matrix

The resulting matrix is conceptually:

| Capability | Ollama direct | Ollama Mellea | MLX direct | MLX Mellea | Unsloth direct | Unsloth Mellea |
|---|---|---|---|---|---|---|
| availability | | | | | | |
| identity | | | | | | |
| generation | | | | | | |
| streaming | | | | | | |
| structured | | | | | | |
| tools | | | | | | |
| chat | N/A | | N/A | | N/A | |
| instruct | N/A | | N/A | | N/A | |
| requirements | N/A | | N/A | | N/A | |
| IVR | N/A | | N/A | | N/A | |

Blank cells are not evidence and therefore cannot be interpreted as PASS.

## 11. Code layout

Create:

    tools/workshop/workshop_tools/providers.py
    tools/workshop/workshop_tools/certification.py

Extend:

    tools/workshop/workshop_tools/cli.py

Tests:

    tests/workshop/test_providers.py
    tests/workshop/test_certification.py
    tests/workshop/test_provider_cli.py

Runtime acceptance tests:

    tests/runtime/test_ollama_runtime.py
    tests/runtime/test_mlx_runtime.py
    tests/runtime/test_unsloth_runtime.py
    tests/runtime/test_mellea_provider_runtime.py

Receipts:

    receipts/provider-certification/
      granite.ollama.json
      granite.mlx.json
      granite.unsloth.json

## 12. Receipt contract

Each receipt records:

    schemaVersion
    profile
    provider
    protocol
    model.logical
    model.providerId
    endpoint
    startedAt
    completedAt
    environment
    providerProbes
    melleaProbes
    certification.status
    certification.reason
    fallbackUsed
    melleaRevision
    workshopRevision

Mandatory invariant:

    fallbackUsed == false

## 13. Probe result contract

Each probe records:

    id
    status
    durationMs
    requestSummary
    responseSummary
    errorClass
    errorMessage
    metadata

Secrets and authorization tokens must never be written to receipts.

## 14. CLI

Extend `workshopctl` with:

    workshopctl provider list

    workshopctl provider inspect PROFILE

    workshopctl provider certify PROFILE

    workshopctl provider certify-all

    workshopctl provider receipt PROFILE

Examples:

    workshopctl provider inspect granite.ollama

    workshopctl provider certify granite.mlx

A certification command exits non-zero on:

- failed core probes;
- unavailable provider;
- wrong model;
- detected fallback;
- invalid receipt.

A provider with explicit advanced `UNSUPPORTED` capabilities may exit zero
only when its derived status is `certified_with_limitations`.

## 15. Provider configuration loader

Provider settings are loaded exclusively from:

    settings/providers/ollama.yaml
    settings/providers/mlx.yaml
    settings/providers/unsloth.yaml

The runtime harness must not hard-code substitute provider identities.

## 16. Task 1 — Certification data model

Implement:

- ProviderProfile
- ProbeResult
- CertificationReceipt
- certification status derivation
- deterministic JSON serialization

TDD requirements:

- PASS serialization
- UNSUPPORTED serialization
- UNAVAILABLE serialization
- deterministic probe order
- fallbackUsed must default false
- receipt rejects fallbackUsed true for workshop certification

Commit:

    feat(certification): add provider certification evidence model

## 17. Task 2 — Provider loader + CLI inspection

Implement configuration loading from the three existing provider YAML files.

Commands:

    workshopctl provider list
    workshopctl provider inspect PROFILE

Tests require:

- exactly three provider profiles
- profile uniqueness
- exact model identity
- no fallback
- unknown profile returns non-zero

Commit:

    feat(providers): add runtime provider registry

## 18. Task 3 — Ollama direct certification

Preflight:

    ollama executable
    runtime availability
    exact granite4.1:3b model presence

Do not pull or substitute another model silently.

Direct probes:

- model discovery
- generation
- streaming
- structured/JSON
- tool declaration/calling
- malformed request
- unknown model

Persist:

    receipts/provider-certification/granite.ollama.json

No Mellea certification occurs until direct provider evidence exists.

Commit:

    test(runtime): certify Granite 4.1 through Ollama

## 19. Task 4 — Ollama through Mellea

Use the pinned Mellea checkout.

Use the native Mellea Ollama backend.

Probe:

- backend/session creation
- chat
- instruct
- async
- streaming
- model options
- structured output
- requirements
- validation
- IVR
- tools

Update only the Ollama receipt's Mellea evidence.

Never edit Mellea upstream.

Commit:

    test(runtime): certify Mellea on Granite Ollama

## 20. Task 5 — MLX direct certification

Preflight:

- Apple Silicon runtime
- mlx / mlx-lm availability
- exact configured model
- configured endpoint :8080

The certification harness may connect to an already running MLX server.

If a runner is implemented, it must launch only the configured
`granite.mlx` model.

Direct OpenAI-compatible probes:

    GET /v1/models

    POST /v1/chat/completions

including:

- non-streaming
- streaming
- structured response
- tool declaration
- tool calling
- invalid model
- invalid request

Persist:

    receipts/provider-certification/granite.mlx.json

Commit:

    test(runtime): certify Granite 4.1 through MLX

## 21. Task 6 — MLX through Mellea

Use Mellea OpenAI-compatible backend integration.

Probe the same relevant Mellea matrix used for Ollama.

Important:

Mellea compatibility must use the MLX endpoint explicitly.

No provider alias may resolve to Ollama or Unsloth.

Commit:

    test(runtime): certify Mellea on Granite MLX

## 22. Task 7 — Unsloth direct certification

Preflight:

    http://127.0.0.1:8888/v1

Require:

    /v1/models

and specifically certify:

    /v1/chat/completions

Prior success of `/v1/responses` alone is not sufficient for Mellea
OpenAI-backend compatibility.

Probe:

- model discovery
- chat completion
- streaming
- structured output
- tool declaration/calling
- invalid request
- invalid model

Persist:

    receipts/provider-certification/granite.unsloth.json

Commit:

    test(runtime): certify Granite 4.1 through Unsloth

## 23. Task 8 — Unsloth through Mellea

Use Mellea OpenAI-compatible backend integration.

Probe the Mellea matrix.

If `/v1/chat/completions` does not conform sufficiently for Mellea:

- record exact failure;
- classify the relevant capability;
- do not route to `/v1/responses` implicitly;
- do not route to another provider.

A workshop-owned explicit adapter may be proposed later if required.

Commit:

    test(runtime): certify Mellea on Granite Unsloth

## 24. Task 9 — Certification aggregation

Implement:

    workshopctl provider certify-all

The command runs providers independently.

One provider failing must not stop evidence collection for the others.

Final exit code is non-zero if any requested provider lacks acceptable
certification status.

Generate a matrix summary from receipts.

Commit:

    feat(certification): aggregate provider certification matrix

## 25. Task 10 — Settings materialization from evidence

Only after receipts exist may provider overlays change:

    certification.status: pending

to one of:

    certified
    certified_with_limitations
    failed
    unavailable

The update must be evidence-driven.

Tests ensure:

- no `certified` status without a matching receipt;
- receipt profile equals settings profile;
- receipt model equals configured model;
- fallbackUsed is false.

Commit:

    feat(providers): materialize runtime certification status

## 26. Task 11 — Capability catalog integration

Provider certification updates the provider evidence dimension of relevant
Mellea capabilities.

Do not mark all Mellea capabilities provider-certified.

Only capabilities that actually have matching receipt evidence may change.

Commit:

    feat(authority): link provider receipts to capability evidence

## 27. Completion gate

Run:

    uv sync --project tools/workshop --group dev

    uv run --project tools/workshop \
      python -m pytest tests/workshop -v

    uv run --project tools/workshop \
      python -m pytest tests/runtime -v

    uv run --project tools/workshop \
      workshopctl authority attest \
      --checkout /Users/cestari/Developer/mainframe/upstreams/generative-computing/mellea

    uv run --project tools/workshop \
      workshopctl coverage check

    uv run --project tools/workshop \
      workshopctl provider certify-all

Required invariants:

    MELLEA_ATTESTATION=PASS
    COVERAGE=PASS
    fallbackUsed=false for every receipt

Every provider must end in one explicit status.

No provider remains ambiguously `pending` after it has been requested for
certification.

## 28. Out of scope

This plan does not yet implement:

- Open WebUI
- OIKB
- MCPO
- Computer
- Open Terminal
- generator materialization
- PostgreSQL migration
- full Mellea capability catalog expansion unrelated to tested provider
  behavior

Those remain separate boundaries.

## 29. Execution order

Execute strictly:

    data model
       ↓
    provider registry
       ↓
    Ollama direct
       ↓
    Ollama + Mellea
       ↓
    MLX direct
       ↓
    MLX + Mellea
       ↓
    Unsloth direct
       ↓
    Unsloth + Mellea
       ↓
    aggregate receipts
       ↓
    materialize evidence
       ↓
    update capability evidence
       ↓
    completion gate

## 30. Safety and provenance invariants

- No secrets in receipts.
- No silent provider fallback.
- No automatic substitution of models.
- No mutation of pinned Mellea.
- Runtime failure is evidence, not a reason to bypass the provider.
- A configured endpoint is not proof of runtime availability.
- A provider PASS is not automatically a Mellea PASS.
- `/v1/responses` success is not proof of `/v1/chat/completions`.
- Receipts are evidence artifacts, not desired-state authority.
