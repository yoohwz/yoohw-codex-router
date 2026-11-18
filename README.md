# YoOhw Codex Router

A small, read-only advisor that tells a Human operator which **Codex model + reasoning effort** to select for the current phase of a YoOhw engineering task.

The router does **not** launch Codex, mutate product repositories, create task state, call GitHub at runtime, or maintain a second governance system.

## Why

YoOhw repositories already encode risk and workflow phase, but Codex Local App model/effort selection is still manual. The router bridges that gap:

> **semantic risk -> minimum model capability**  
> **unresolved judgment -> reasoning effort**  
> **workflow phase -> upgrade/downgrade timing**

Repository/task authority always wins over global defaults.

## MVP support

- Blacklist Manager (`wc-blacklist-manager`; Premium/Global supported when canonical Core policy is locally available)
- Advanced Order Actions (`wc-advanced-order-actions`)

Customer Intelligence, Order Splitter, Support Portal and other repositories are intentionally deferred until dedicated adapters and fixtures are added.

## Install locally

From this repository:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Then `yoohw-profile` is available in that environment.

You can also run without installing:

```sh
PYTHONPATH=src python -m yoohw_codex_router --help
```

## Usage

From a supported product repository:

```sh
yoohw-profile BM-0152
```

Or from anywhere:

```sh
yoohw-profile BM-0152 --repo ~/Herd/wc-blacklist-manager
```

The task ID may be omitted when the current branch is recognizable, for example `bm-0152-*` or `aoa-269-*`:

```sh
yoohw-profile
```

Independent review:

```sh
yoohw-profile BM-0152 --review
```

Compact output for quick operator use:

```sh
yoohw-profile BM-0152 --compact
# gpt-6.2-sol / MEDIUM
```

Structured output:

```sh
yoohw-profile BM-0152 --json
```

## Example

```text
YoOhw Codex Profile Advisor

Repository: wc-blacklist-manager
Task: BM-0152
Lane: DEEP_BM
Phase: IMPLEMENTATION
Authority: BM canonical compute policy + lane/status

----------------------------------------
SELECT IN CODEX APP
Model:  gpt-6.2-sol
Effort: MEDIUM
----------------------------------------

Why
- Deep implementation may downgrade to Sol/MEDIUM after the architecture/boundary is settled.

Escalation target: gpt-6.2-sol / HIGH

Escalate when
- security/auth/payment/licensing/privacy/persistence/concurrency semantics become unresolved
- a compatibility-sensitive shared contract or architecture boundary becomes ambiguous
- the approved implementation boundary no longer fits repository evidence

Independent review floor: gpt-6.2-sol / HIGH
```

## Blacklist Manager policy source

The router verifies the canonical `docs/CODEX-EXECUTION-PROFILES.md` before recommending a profile. For Premium or Global task authority, keep Core as a sibling checkout or set:

```sh
export BM_CORE_DIR=~/Herd/wc-blacklist-manager
```

The router deliberately does not invoke `run-bm.sh --dry-run`: that launcher performs Git fetch/ref/worktree validation, while this tool's runtime contract is local and read-only.

## AOA policy source

The router reads AOA's current `docs/workflow.md` compute table. It recommends Sol/MEDIUM for implementation or correction and Sol/HIGH for optional complex discovery and independent Controlled review.

AOA tasks are GitHub Issues. For offline advice, pass a local Markdown snapshot of the admitted Issue inside the target checkout. Include the risk lane and current execution status (for example, `Risk lane: Controlled` and `Status: IMPLEMENTING`). The snapshot is advisory input and should be checked against the Issue and PR. For example:

```sh
yoohw-profile AOA-269 --repo ~/Herd/wc-advanced-order-actions --task-file local-aoa-269.md
```

Pass `--review` to request review compute or include a `Codex launch contract` with `Workflow mode: DISCOVERY_ONLY` for an authorized complex discovery run. During rollout, the advisor follows the verified 6.1 or 6.2 Sol mapping actually present in each checkout.

## Development

No runtime dependencies are required.

```sh
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

See [`docs/ROUTING-CONTRACT.md`](docs/ROUTING-CONTRACT.md) for precedence, read-only boundaries and fail-closed behavior.
