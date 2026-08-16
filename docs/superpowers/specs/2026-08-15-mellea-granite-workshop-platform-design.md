# Mellea + Granite Workshop Platform Design

Status: APPROVED-DESIGN
Date: 2026-08-15

## 1. Purpose

Evolve IBM/opensource-ai-workshop into a runtime-first generative
computing workshop and development platform.

Open WebUI is an experience layer, not the runtime authority.

Before Open WebUI, the platform must provide independently functional:

- Granite inference;
- Mellea generative computing;
- code and document generation;
- tools;
- MCP;
- MCPO;
- knowledge/RAG;
- CLI development workflows;
- computer/terminal integration;
- public authenticated APIs.

## 2. Source authority

Workshop upstream base:

- repository: IBM/opensource-ai-workshop
- revision: 1b1ddaa486ce40dc8b444da61d9b09b6643eed52
- tree: b5b02a0e92218ca4f2f1e40cd54056afc88afe59

Mellea authority:

- repository: generative-computing/mellea
- revision: 853b04fe572b3f8d2947c56750c883aeae12ea0b
- mode: pinned/read-only upstream

The workshop owns:

- capability catalog;
- desired settings;
- generators;
- provider overlays;
- runtime profiles;
- authorization;
- labs;
- generated examples;
- integration adapters;
- receipts.

Mellea is not modified merely to satisfy workshop integration.

A Mellea fork is permitted only when evidence demonstrates that an
adapter or overlay cannot correctly implement a required capability.

## 3. Architectural authority model

The platform has three canonical layers:

1. capability catalog
2. desired settings
3. generated materialization

Flow:

    pinned Mellea source
            |
            v
    discovery verifier
            |
            v
    capability catalog
            |
            +------ desired workshop settings
            |                 |
            +--------+--------+
                     |
                     v
                 generators
                     |
        +------------+-------------+
        |            |             |
       code       documents       config
        |            |             |
       tests        labs        providers/tools
        |
        v
    validation
        |
        v
    receipts + coverage

The discovery verifier audits upstream coverage.

It does not silently make upstream internals public API.

Public workshop contracts are versioned explicitly.

## 4. Runtime-first architecture

Granite 4.1 is certified before Open WebUI.

Primary model:

    IBM Granite 4.1 3B

Required provider profiles:

    granite.ollama
    granite.mlx
    granite.unsloth

Logical topology:

                     Granite 4.1
                          |
              +-----------+-----------+
              |           |           |
           Ollama        MLX       Unsloth
              |           |           |
              +-----------+-----------+
                          |
                        Mellea
                          |
                       m serve
                          |
                  public API surface

There is no silent provider fallback.

A provider must be explicitly selected.

Failure of one provider does not silently select another provider.

## 5. Provider identities

### Ollama

Logical model:

    granite4.1:3b

Use:

- native Mellea Ollama backend where appropriate;
- OpenAI-compatible surface where explicitly tested;
- workshop local development baseline.

### MLX

Logical model:

    ibm-granite/granite-4.1-3b

Use:

- mlx-lm;
- Apple Silicon / Metal;
- OpenAI-compatible adapter into Mellea.

MLX-specific model information not represented by the pinned upstream
ModelIdentifier is stored in workshop-owned provider overlays.

### Unsloth

Logical model family:

    unsloth/granite-4.1-3b-GGUF

Use:

- local Unsloth Studio runtime;
- OpenAI-compatible adapter when certified;
- GGUF/BF16 and supported quantized profiles.

Unsloth capability certification is independent of Ollama and MLX.

## 6. Provider certification contract

Each provider is independently tested for applicable capabilities:

- model discovery;
- plain generation;
- streaming;
- structured output;
- tool calling;
- model identity;
- context limits;
- health;
- failure behavior.

Mellea certification then tests:

- chat;
- instruct;
- async;
- streaming/lazy thunks;
- requirements;
- validation;
- rejection sampling;
- Instruct-Validate-Repair;
- structured Pydantic output;
- grounding context;
- user variables;
- ICL examples;
- prefixes;
- model options;
- tools;
- documents;
- multimodal capability where supported.

Unsupported provider features are explicitly classified.

They are never reported as passing through fallback.

## 7. Mellea capability catalog

The catalog covers the complete pinned repository.

At minimum it classifies:

### Runtime

- sessions;
- contexts;
- chat;
- instruct;
- act/aact;
- async;
- streaming;
- ModelOutputThunk;
- validation;
- query;
- transform;
- powerups.

### Generative programming

- requirements;
- req/check;
- custom validators;
- rejection sampling;
- IVR;
- sampling strategies;
- budget forcing;
- feedback;
- majority voting;
- SoFAI.

### Code generation

- @generative;
- GenerativeStub;
- GenSlot;
- m decompose;
- m fix;
- code requirements;
- typed/Pydantic outputs;
- code execution;
- unit-test evaluation.

### Documents and structured data

- Document;
- RichDocument;
- Docling;
- PDF;
- Markdown;
- DOCX;
- PPTX;
- HTML;
- tables;
- MObject;
- Query;
- Transform;
- Mify.

### Knowledge and RAG

- grounding documents;
- FAISS;
- Granite embedding/retriever components;
- relevance filtering;
- grounded answer generation;
- citation/provenance validation;
- RAG intrinsics.

### Tools and agents

- MelleaTool;
- native tools;
- shell;
- interpreter;
- execution environments;
- ReAct;
- agents;
- MCP;
- HTTP MCP;
- SSE MCP;
- stdio MCP;
- Smolagents interoperability.

### Specialized capabilities

- aLoRA;
- Granite Switch;
- intrinsics;
- policy guardrails;
- factuality;
- uncertainty;
- answerability;
- hallucination detection;
- query rewriting;
- query clarification;
- citations.

### Multimodal

- image inputs;
- vision examples;
- audio blocks;
- audio-text workflows.

### Service and engineering

- m serve;
- m eval;
- m decompose;
- m fix;
- m alora;
- plugins;
- logging;
- metrics;
- tracing;
- telemetry;
- documentation autogeneration;
- CLI reference generation;
- coverage auditing.

## 8. Capability evidence levels

Presence of a file is not sufficient to call a capability operational.

Each capability records independent evidence:

- SOURCE
- DOCUMENTED
- EXAMPLED
- TESTED
- PROVIDER_CERTIFIED
- WORKSHOP_MATERIALIZED

Possible statuses include:

- UPSTREAM_AS_IS
- WORKSHOP_NATIVE
- WORKSHOP_ADAPTED
- EXTERNAL_PROVIDER_REQUIRED
- EXTERNAL_SERVICE_REQUIRED
- UNSUPPORTED_PROVIDER
- MANUAL_INTERACTIVE
- BLOCKED
- UPSTREAM_DEFECT

## 9. Desired settings architecture

Canonical settings tree:

    settings/
    ├── workshop.yaml
    ├── models.yaml
    ├── providers/
    │   ├── ollama.yaml
    │   ├── mlx.yaml
    │   └── unsloth.yaml
    ├── mellea/
    │   ├── sessions.yaml
    │   ├── generation.yaml
    │   ├── requirements.yaml
    │   ├── sampling.yaml
    │   └── serve.yaml
    ├── authorization/
    │   ├── roles.yaml
    │   ├── levels.yaml
    │   ├── permissions.yaml
    │   └── policies.yaml
    ├── tools/
    │   ├── native.yaml
    │   ├── execution.yaml
    │   ├── mcp.yaml
    │   └── mcpo.yaml
    ├── knowledge/
    │   ├── oikb.yaml
    │   ├── rag.yaml
    │   └── corpora.yaml
    └── observability/
        ├── logging.yaml
        ├── metrics.yaml
        └── tracing.yaml

Settings are schemas and desired state.

Generated runtime files are not used as the source of truth.

## 10. Authorization

Public API exposure is allowed.

Exposure does not imply authorization.

Canonical authorization model:

    Tenant
      |
      +-- Workspace
            |
            +-- Membership
                  |
                  +-- User
                  +-- Role
                  +-- Level
                         |
                         v
                    Permissions
                         |
                         v
                    Entitlements

Authorization combines RBAC and ABAC.

Effective authorization may depend on:

- tenant_id;
- workspace_id;
- user_id;
- membership;
- role;
- level;
- capability;
- model;
- environment;
- execution risk;
- resource ownership.

## 11. Permission targets

Authorization applies independently to:

- model discovery;
- model invocation;
- Mellea programs;
- m serve endpoints;
- native tools;
- MCP servers/tools;
- MCPO;
- knowledge bases;
- corpora;
- RAG;
- Computer;
- Open Terminal;
- filesystem execution;
- package installation;
- administration;
- settings mutation.

## 12. Settings inheritance

Effective settings resolve in this order:

    global defaults
          |
          v
    tenant settings
          |
          v
    workspace settings
          |
          v
    role / level policy
          |
          v
    permitted user overrides
          |
          v
    effective settings

Every resolved configuration must be inspectable.

## 13. Persistence boundary

Open WebUI persistence is not the domain authority.

The platform defines stable domain contracts for:

- users;
- tenants;
- workspaces;
- memberships;
- roles;
- levels;
- permissions;
- entitlements.

Persistence uses adapters.

Initial compatibility may use Open WebUI SQLite.

Target persistence is PostgreSQL.

The SQLite -> PostgreSQL migration must not change public identifiers,
permission names, capability IDs, Mellea program contracts, or APIs.

## 14. Tool plane

Tools must function independently of Open WebUI.

Topology:

    Mellea native tools
            |
    MCP ----+---- MCPO
            |
    execution environments
            |
    shared tool registry
            |
       +----+---------+
       |              |
      CLI          Computer
                       |
                  Open Terminal

Open WebUI later consumes the same tool plane.

## 15. Execution security

Execution settings must distinguish declared policy from enforced policy.

No UI or API may claim filesystem/network isolation when the selected
execution environment does not actually enforce it.

Policy metadata therefore records:

- requested restrictions;
- actively enforced restrictions;
- enforcement gaps;
- execution tier;
- approval requirements;
- audit result.

## 16. Knowledge plane

Knowledge exists before Open WebUI.

Sources include:

- complete workshop repository;
- complete pinned Mellea corpus;
- workshop resources;
- labs;
- documents;
- PDFs;
- generated documentation;
- approved project repositories.

Flow:

    source corpus
        |
        v
       OIKB
        |
        v
    canonical knowledge materialization
        |
        +-- Mellea RAG
        +-- CLI
        +-- evaluations
        +-- Open WebUI Knowledge

Indexes are derived/rebuildable artifacts.

Source provenance is authoritative.

## 17. Generator

The workshop owns a document + code generator.

Inputs include:

- natural-language request;
- specification;
- existing source;
- document;
- repository;
- template;
- Mellea capability;
- workshop recipe.

Outputs may include:

- Python;
- Markdown;
- MDX;
- JSON;
- YAML;
- notebooks;
- tests;
- API services;
- M programs;
- MCP configuration;
- MCPO configuration;
- Open WebUI configuration;
- generated documentation;
- receipts.

Generation flow:

    request
       |
       v
    specification
       |
       v
    requirements
       |
       v
    Mellea generative program
       |
       v
    generation strategy
       |
       v
    Granite provider
       |
       v
    validation
       |
       +-- optional execution
       |
       v
    repair
       |
       v
    artifact
       |
       v
    documentation
       |
       v
    receipt

## 18. Generation profiles

Required profiles:

- simple
- structured
- validated
- generative-function
- document
- rag
- codegen
- agent
- transform
- multimodal
- production

Profiles are composable.

## 19. Generated materialization

Generated outputs live separately from desired state.

Target tree:

    generated/
    ├── runtime/
    │   ├── providers/
    │   ├── programs/
    │   └── services/
    ├── api/
    ├── tools/
    ├── mcp/
    ├── mcpo/
    ├── knowledge/
    ├── computer/
    ├── openwebui/
    ├── examples/
    ├── labs/
    ├── docs/
    └── tests/

Generated artifacts carry provenance.

Manual edits to generated files are not authoritative.

## 20. Artifact provenance

Every generated artifact records enough information to reconstruct why
it exists.

Required provenance includes:

- generator version;
- workshop revision;
- Mellea revision;
- settings hash;
- capability IDs;
- provider;
- model ID;
- immutable model revision where available;
- generation strategy;
- validation result;
- execution result where applicable.

## 21. Documentation generation

Documentation is generated and audited together with code.

The workshop adopts the same architectural principle demonstrated by
Mellea's docs-autogen tooling:

    source
       |
       v
    capability manifest
       |
       v
    generator
       |
       +-- code
       +-- examples
       +-- labs
       +-- API reference
       +-- CLI reference
       +-- documentation
       |
       v
    coverage audit

Capabilities may not silently exist outside the catalog.

Documentation may not claim unsupported capabilities.

## 22. Open WebUI boundary

Open WebUI comes after runtime certification.

Experience topology:

                    Open WebUI
                   Web + Desktop
                        |
          +-------------+-------------+
          |             |             |
       Mellea        Knowledge      Tools
       m serve         OIKB        MCP/MCPO
          |
          +------ Computer/Open Terminal

Open WebUI is:

- user experience;
- model/tool/knowledge consumer;
- workspace surface.

Open WebUI is not:

- model runtime authority;
- Mellea authority;
- authorization-domain authority;
- canonical knowledge provenance authority.

## 23. Capability completion gate

A workshop capability is COMPLETE only when applicable evidence exists:

SOURCE
- upstream provenance

CATALOG
- capability entry
- classification

SETTINGS
- schema
- defaults
- validation

RUNTIME
- provider selection
- capability result

EXAMPLE
- runnable representative example

GENERATOR
- generated artifact when applicable

TEST
- unit/integration/acceptance as applicable

DOCUMENTATION
- explanation
- reference
- runnable recipe

AUTHORIZATION
- scope
- permission
- policy

RECEIPT
- revisions
- settings
- provider
- result

## 24. Coverage invariant

Target invariant:

    source capability
          =
    cataloged capability
          =
    settings capability
          =
    documented capability
          =
    tested/classified capability

A discovered upstream capability without classification fails coverage.

A public workshop capability without authorization metadata fails coverage.

## 25. Implementation order

Implementation is intentionally runtime-first:

1. repository authority and locks
2. Mellea capability discovery verifier
3. capability catalog
4. settings schemas
5. authorization schemas
6. provider model overlays
7. Ollama certification
8. MLX certification
9. Unsloth certification
10. Mellea provider profiles
11. Mellea capability acceptance
12. generator foundation
13. simple/structured/validated generation
14. document/code generation
15. native tools
16. MCP
17. MCPO
18. OIKB/knowledge
19. RAG
20. CLI development surfaces
21. Computer/Open Terminal
22. m serve public surfaces
23. Open WebUI Web/Desktop
24. SQLite compatibility
25. PostgreSQL migration adapter
26. complete labs/examples materialization
27. coverage and release receipts

## 26. Non-negotiable invariants

- Pinned Mellea upstream remains immutable.
- No silent provider fallback.
- Granite 4.1 provider identity is explicit.
- Open WebUI is not required for core runtime operation.
- Tools work outside Open WebUI.
- Knowledge works outside Open WebUI.
- Authorization is independent of Open WebUI persistence.
- Public API does not imply public permission.
- Generated artifacts are not desired-state authority.
- Unsupported provider capabilities are explicitly classified.
- Execution enforcement gaps are represented honestly.
- Every active capability has provenance.
