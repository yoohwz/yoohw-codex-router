# Routing Contract v0.1

## Purpose

`yoohw-profile` advises a Human operator which Codex model and reasoning effort to select for the current substantive workflow phase. It is intentionally not an orchestrator, launcher, task database, model-history ledger, or replacement for repository governance.

## Precedence

The router resolves compute in this order:

1. explicit repository/task compute authority;
2. independent-review floor;
3. repository lane/risk policy;
4. current workflow phase;
5. built-in minimum qualified fallback for that supported repository.

Heuristics do not override canonical task or repository authority. v0.1 intentionally contains no numeric complexity score and no AI classifier.

## Core rule

- **Semantic risk selects the minimum model capability.**
- **Unresolved judgment selects reasoning effort.**
- **Workflow phase determines when compute can downgrade or must upgrade again.**

The normal phase pattern is:

```text
Deep Discovery / Architecture -> Sol / HIGH
Settled deterministic implementation -> Terra / MEDIUM
Mechanical evidence/documentation -> Luna / LOW when repository authority permits
Independent Deep review -> Sol / HIGH
```

This pattern is not itself authority. Repository/task policy may deliberately keep a stronger profile, and that explicit profile wins.

## Blacklist Manager adapter

The adapter verifies the canonical `docs/CODEX-EXECUTION-PROFILES.md` markers before routing. It never invokes `run-bm.sh`, because the canonical launcher performs Git fetch/ref/worktree validation even in dry-run mode.

Current mapping:

| Authority | Profile |
| --- | --- |
| `STANDARD_BM` Run | GPT-5.6 Terra / MEDIUM |
| `DEEP_BM` + `READY` Discovery/Architecture | GPT-5.6 Sol / HIGH |
| `DEEP_BM` + `IMPLEMENTING`/legacy `CHANGES_REQUIRED` | GPT-5.6 Terra / MEDIUM |
| `TECHNICAL_REVIEW_REQUIRED` / explicit review | GPT-5.6 Sol / HIGH |
| ChatGPT/Human gates | No Codex action |

For Premium/Global task authority, the adapter resolves Core policy locally through `BM_CORE_DIR` or a sibling `wc-blacklist-manager` checkout. It does not use network discovery.

## Advanced Order Actions adapter

AOA owns its qualified model registry in `docs/codex/aoa_compute_policy.py`. The adapter validates the currently qualified Luna/Terra/Sol tier mapping before routing.

An explicit `## Codex launch contract` is authoritative and wins over global defaults. `Baseline`, `Escalation`, and `Downgrade` blocks are presented as operator guidance but are not auto-selected; their conditions must be observed by the operator/workflow before switching profiles.

Independent AOA review has a DEEP/HIGH floor. XHIGH remains exceptional and must be explicitly approved by AOA authority.

## Read-only boundary

Runtime operations are limited to:

- reading local Git identity/branch;
- reading task Markdown;
- reading local compute-policy files;
- rendering a recommendation.

No `git fetch`, checkout, branch mutation, commit, push, GitHub API call, Codex launch, target file edit, environment mutation, or model-state persistence is part of v0.1 routing.

## Fail-closed conditions

Return an error instead of a recommendation when:

- the target repository is unsupported;
- the task file is missing or ambiguous;
- required task fields are missing/duplicated;
- canonical compute policy is missing or no longer matches the adapter's verified contract;
- an AOA task requests an unqualified model/effort pair;
- review is requested from an invalid BM review state.

A non-Codex Human/ChatGPT gate is not an error; the router returns `NO_CODEX_ACTION`.
