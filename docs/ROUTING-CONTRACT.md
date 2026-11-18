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

BM and AOA both use Sol/MEDIUM for ordinary implementation and correction, and Sol/HIGH for repository-defined complex discovery and independent review. The adapter verifies each repository's phase table, selecting 6.1 or 6.2 Sol according to the checked-out policy. A missing row, mixed model family or different effort fails closed. Astra remains an exception handled under the target workflow's existing authority.

## Blacklist Manager adapter

The adapter reads `docs/CODEX-EXECUTION-PROFILES.md` from Core. It never invokes `run-bm.sh`, because the launcher performs Git fetch/ref/worktree validation even in dry-run mode.

| Authority | Effort |
| --- | --- |
| `STANDARD_BM` Run | MEDIUM |
| `DEEP_BM` + `READY` Discovery/Architecture | HIGH |
| `DEEP_BM` + `IMPLEMENTING`/legacy `CHANGES_REQUIRED` | MEDIUM |
| `TECHNICAL_REVIEW_REQUIRED` / explicit review | HIGH |
| Current Human or applicable historical ChatGPT gate | No Codex action |

For Premium/Global task authority, the adapter resolves Core policy locally through `BM_CORE_DIR` or a sibling `wc-blacklist-manager` checkout. It does not use network discovery.

## Advanced Order Actions adapter

The adapter reads the **Compute and delegation** table in `docs/workflow.md`. A local task snapshot represents the admitted GitHub Issue and current status and follows the `Fast` or `Controlled` lanes. The router uses an explicit, policy-compatible `Codex launch contract` when supplied. A discovery-only profile uses at least HIGH, and an explicit XHIGH profile requires a specific unresolved technical reason. Legacy task snapshots with an obsolete lane or incompatible profile require the operator to consult the task's admitted workflow.

An explicit review recommendation or `TECHNICAL_REVIEW_REQUIRED` uses Sol/HIGH. The advisor provides compute guidance only. Issue/PR authority, fresh isolated reviewer context, exact candidate binding, and Ready and CI rules stay with the actual AOA workflow. A task on a recorded non-execution hold returns no action, including with `--review`.

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
- an AOA task requests a profile outside the verified policy or omits its current lane/status;
- review is requested from an invalid BM review state.

A non-Codex Human/ChatGPT gate is not an error; the router returns `NO_CODEX_ACTION`.
