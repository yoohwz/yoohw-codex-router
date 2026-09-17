# YoOhw Codex Router — Repository Contract

This repository provides a read-only operator advisor for selecting Codex model and reasoning effort in YoOhw engineering workflows.

## Non-negotiable invariants

- The router never launches Codex.
- The router never writes to a target product repository.
- The router never creates or mutates task/workflow state.
- Runtime routing is local/offline by default; do not add GitHub/API/network discovery merely to select compute.
- Repository/task authority outranks global defaults and heuristics.
- Unknown or changed compute authority fails closed with `PROFILE_REQUIRED` rather than guessing.
- Model selection is based on repository risk authority and workflow phase; effort selection reflects unresolved judgment. Do not introduce a numeric complexity score.
- Expensive compute is phase-scoped. A Deep task does not imply Deep compute for every implementation/test/documentation action.
- Independent technical review keeps its repository-defined compute floor and must not be downgraded because implementation was downgraded.

## MVP scope

The v0.1 MVP supports:

- Blacklist Manager (`wc-blacklist-manager`, plus local Core-policy resolution for Premium/Global task authority);
- Advanced Order Actions (`wc-advanced-order-actions`).

Other repositories require explicit adapters and tests before they are considered supported.

## Development

Use Python standard library only unless a dependency has a concrete, reviewed benefit. Run:

```sh
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

Keep adapters small. Prefer parsing durable repository authority over keyword heuristics. Every new routing rule needs deterministic fixtures for normal, escalation, downgrade and fail-closed behavior where applicable.

Do not merge or release without Human Owner authorization.
