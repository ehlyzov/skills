---
name: service-knowledge-contour
description: Bootstrap, refresh, audit, promote, and prune the minimal knowledge contour for a single service repository. Use this when a service repo lacks a stable agent/human operating model, when service knowledge has drifted, or when a change affects topology, verification, or operational risk. Do not use for ordinary feature work unless the change triggers a knowledge update.
---

# Purpose

Maintain a minimal, high-signal knowledge contour for one service repository.

This skill exists to:

- reduce search cost;
- reduce hallucination risk;
- localize change surface faster;
- strengthen the verification loop;
- keep startup context cheap for agents and humans;
- prevent documentation sprawl;
- keep repository knowledge fresh through refresh, audit, promotion, and pruning.

This skill is not a documentation factory.

Do not create files that do not have:
- a clear read path,
- a clear update trigger,
- a clear operational value.

# Scope

This skill is for a single service repository.

It is not for:
- monorepo governance;
- organization-wide standards;
- generic documentation scaffolding;
- optional knowledge layers created "for future use".

# Hard rules

1. One knowledge type must have one canonical home.
2. Canonical knowledge must stay small.
3. Generated artifacts must be clearly separated from canonical artifacts.
4. Event-driven docs must not be created during bootstrap unless a real trigger exists.
5. Do not create empty folders or placeholder docs "just in case".
6. Do not split one operational knowledge type across multiple markdown files unless the split is already justified by real overload.
7. Unresolved durable facts must live only in one gap registry.
8. Do not preserve stale docs out of politeness.
9. Prefer delete over archive unless history matters operationally.
10. Do not invent commands, paths, boundaries, APIs, ownership, or verification results.

# Canonical structure

## Mandatory canonical core

Create or maintain only these canonical files by default:

- `AGENTS.md`
- `CLAUDE.md`
- `docs/service/SERVICE_MAP.md`
- `docs/service/VERIFY.md`
- `docs/service/knowledge-gaps.yaml`

## Mandatory generated layer

Create or maintain these generated artifacts:

- `docs/service/generated/change-surface.json`
- `docs/service/generated/hotspots.md`
- `docs/service/generated/health-report.json`

Generated artifacts are rebuildable and are never source of truth.

## Event-driven docs

Create only when triggered by real repository history or repeated operational need:

- `docs/service/ADR/*`
- `docs/service/runbooks/*`
- `docs/service/GLOSSARY.md`
- `docs/service/migrations/*`
- `docs/service/incidents/*`
- `.claude/agents/*`

Do not create any of these during bootstrap without evidence.

## Forbidden-by-default artifacts

Do not create during bootstrap:

- empty ADR trees;
- empty runbook directories;
- ownership docs;
- separate commands docs;
- separate local-dev docs;
- separate testing docs;
- separate quality-gates docs;
- separate change-evidence docs;
- module-by-module markdown maps;
- speculative future architecture docs;
- eval placeholders;
- policy documents that only restate the contour rules.

# Canonical file contracts

## 1. `AGENTS.md`

This is startup context only.

It must stay short.

Allowed content:
- non-negotiable work rules;
- pointer to canonical docs;
- safe-edit expectations;
- verification expectation;
- explicit prohibition on guessing commands, paths, APIs, or results.

Forbidden content:
- long architecture prose;
- copied command catalogs;
- runbook content;
- historical narrative;
- repeated troubleshooting notes;
- scattered TODO placeholders.

## 2. `CLAUDE.md`

This is a thin vendor wrapper.

Required behavior:
- mirror or import the startup contract;
- add only tool-specific behavior if it is real and necessary;
- point to the same canonical knowledge as `AGENTS.md`.

Forbidden behavior:
- forking the project canon;
- maintaining alternate architecture truth;
- maintaining alternate verification truth.

## 3. `docs/service/SERVICE_MAP.md`

This is the single canonical structural document for the service.

It must help a reader localize change surface and risk quickly.

Required sections:
- service purpose in one short paragraph;
- runtime entrypoints;
- top-level module map;
- key boundaries and invariants;
- critical integrations visible from the repo;
- dangerous zones and legacy hotspots;
- references to generated overlays;
- review triggers.

Forbidden content:
- file-by-file encyclopedias;
- copied code listings;
- speculative future architecture;
- debugging diaries;
- historical storytelling that does not affect present work.

By default, hotspots belong here. Do not split them into another canonical file unless the service has already proved that `SERVICE_MAP.md` is overloaded.

## 4. `docs/service/VERIFY.md`

This is the single canonical verification contract.

It must be executable, not vague.

Required sections:
- fastest local setup path;
- narrow verification path;
- full local verification path;
- CI-only checks;
- risk-triggered extra checks;
- required change evidence;
- what cannot be verified locally.

This file is the canonical home for:
- commands that matter for verification or local run;
- quality gates;
- change evidence expectations;
- local-vs-CI verification boundaries.

Forbidden content:
- vague advice like "run relevant tests";
- duplicated command docs elsewhere;
- CI prose with no actionable consequence;
- unverifiable claims.

Do not split verification into separate `commands`, `local-dev`, `testing`, `quality-gates`, or `change-evidence` files by default. That is one knowledge type.

## 5. `docs/service/knowledge-gaps.yaml`

This is the only allowed registry for unresolved durable knowledge gaps.

Each item must include:
- `id`
- `fact`
- `why_missing`
- `owner`
- `created_on`
- `expires_on`
- `promotion_target`
- `status`

Rules:
- unresolved facts must not be scattered across canonical docs;
- gaps without owner are invalid;
- gaps without expiry are invalid;
- expired gaps must fail audit in mandatory contexts.

# Generated layer contract

## `change-surface.json`

Purpose:
- localize likely change surface;
- show adjacent modules and configs;
- indicate likely verification impact.

Signals should include, where inferable:
- runtime entrypoints;
- imports or dependency structure;
- config/build/test files;
- touched-path overlays;
- test adjacency.

If confidence is low, record low confidence. Do not fabricate precision.

## `hotspots.md`

Purpose:
- short human-readable summary of fragile areas.

Should include, where inferable:
- fragile paths;
- low-confidence or low-test areas;
- generated or dangerous code;
- migration-sensitive zones;
- expensive or flaky verification areas.

This is generated guidance, not canon.

## `health-report.json`

Purpose:
- machine-readable contour health.

Must include, where possible:
- broken links;
- dead referenced paths;
- stale gap items;
- invalid commands referenced by canon;
- duplicate-guidance signals;
- oversized canonical docs;
- drift candidates between code changes and canonical docs.

# Modes

Use the lightest mode that solves the real problem.

## Mode 1: bootstrap

Use when:
- the repo has no contour;
- the contour is fragmented or overloaded;
- agent onboarding is expensive because service knowledge is scattered.

Create only the mandatory canonical core and mandatory generated layer.

Do not create event-driven docs without evidence.

## Mode 2: refresh

Use when:
- topology changed;
- entrypoints changed;
- verification commands changed;
- build/test/lint/typecheck/local-run setup changed;
- dangerous zones changed;
- a recent change likely made canonical knowledge stale.

Refresh only the affected canonical files and generated artifacts.

Do not touch unrelated docs.

## Mode 3: audit

Use when:
- checking contour quality;
- preparing a merge gate;
- validating drift;
- reviewing whether canonical knowledge is still usable.

Generate reports and fail conditions.

Do not silently rewrite canon unless explicitly asked.

## Mode 4: promote

Use when:
- a task, incident, bugfix, postmortem, or repeated review confusion produced durable knowledge.

Promotion flow:
1. capture the transient learning;
2. classify it;
3. promote it to exactly one canonical home or one event-driven doc;
4. delete or expire the transient residue.

Classification:
- structural
- verification
- operational
- terminology
- decision
- discard

## Mode 5: prune

Use when:
- docs are stale;
- guidance is duplicated;
- a file has no clear reader anymore;
- a document no longer affects search, decision, or verification paths;
- placeholders have expired;
- a file is mostly dead weight.

Preferred pruning order:
1. delete
2. merge
3. archive

# Trigger model

Update docs only when a real trigger exists.

## Trigger: build/test/lint/typecheck/local-run config changed

Update:
- `docs/service/VERIFY.md`
- generated reports if they derive from these changes

## Trigger: topology, entrypoint, routing, integration boundary, schema shape, or workflow shape changed

Update:
- `docs/service/SERVICE_MAP.md`
- generated reports if they derive from these changes

## Trigger: hotspot path changed or repeated regressions occurred

Update:
- `docs/service/SERVICE_MAP.md`
- `docs/service/VERIFY.md` if verification expectations changed
- create a runbook only if the recovery or handling procedure is repeatable and worth rereading

## Trigger: repeated incident, repeated recovery procedure, or repeated review confusion

Promote into exactly one of:
- runbook
- ADR
- glossary
- migration note
- incident note
- existing canonical core doc

Do not spread one insight across several homes.

## Trigger: repeated domain ambiguity

Create or update:
- `docs/service/GLOSSARY.md`

Only if the ambiguity is recurring and expensive.

## Trigger: long-lived architectural tradeoff

Create or update:
- `docs/service/ADR/*`

Only if the tradeoff is durable and future readers will need it.

# Read-path test

Before creating any new canonical or event-driven knowledge file, verify all of these:

1. Someone will reread it.
2. It changes a search path, decision path, or verification path.
3. It has a clear update trigger.
4. It does not duplicate an existing canonical home.

If any condition fails, do not create the file.

# Promotion model

Durable knowledge must move through this path:

1. a transient finding appears in a task, review, incident, or bugfix;
2. the finding is classified;
3. the finding is promoted to exactly one canonical home;
4. the transient source is deleted, expired, or left explicitly non-canonical.

Never keep the same durable insight indefinitely in both transient notes and canon.

# Pruning model

A document is a prune candidate when:
- relevant code changed but the document did not;
- it duplicates another canonical document;
- it has no clear reader anymore;
- it points to dead paths;
- it is mostly placeholders;
- it no longer affects search, decision, or verification.

If history is not operationally important, delete it.

# Placeholder and uncertainty policy

Uncertainty is allowed only in controlled form.

Rules:
- placeholders are forbidden in `AGENTS.md`;
- placeholders in mandatory canonical docs must be time-bounded;
- unresolved durable uncertainty must be moved to `knowledge-gaps.yaml`;
- free-text TODO noise is forbidden;
- expired placeholders and expired gap items must fail audit.

# Overload split rule

Do not split `SERVICE_MAP.md` or `VERIFY.md` by default.

Split only if there is clear evidence of overload, such as:
- repeated reader confusion;
- persistent review friction;
- unstable navigation because the file became too large;
- two clearly different update rhythms inside one file;
- repeated drift caused by unrelated edits colliding in the same canonical home.

If a split happens:
- define the new canonical boundaries explicitly;
- move the minimum required content;
- remove the old duplicated sections;
- keep one index-level pointer in the original file.

# Audit contract

Audit must check:
- mandatory files exist and are non-empty;
- canonical links resolve;
- referenced paths exist;
- commands referenced in canon still appear valid when they can be checked;
- gap items are not expired;
- forbidden placeholders are absent;
- startup docs do not duplicate canonical docs excessively;
- canonical docs are not oversized beyond their intended use;
- nearby code changed without corresponding canonical refresh;
- event-driven docs still have a valid read path and trigger history.

Audit is not optional in steady state.

# Execution flow

## Phase 1: inspect repository reality

Read, where present:
- root docs;
- runtime entrypoints;
- build/test/lint/typecheck configs;
- CI files;
- existing `AGENTS.md` and `CLAUDE.md`;
- existing service docs.

Infer only what the repository supports.

Do not guess.

## Phase 2: normalize startup layer

Create or repair:
- `AGENTS.md`
- `CLAUDE.md`

Rules:
- compress startup instructions;
- remove durable knowledge from startup docs;
- replace prose with pointers to canon;
- keep tool-specific deltas thin.

## Phase 3: create or repair canonical core

Create or repair:
- `docs/service/SERVICE_MAP.md`
- `docs/service/VERIFY.md`
- `docs/service/knowledge-gaps.yaml`

Rules:
- one fact in one place;
- merge overlapping sections;
- delete ceremonial sections;
- move unresolved durable facts into the gap registry.

## Phase 4: create or refresh generated layer

Create or refresh:
- `docs/service/generated/change-surface.json`
- `docs/service/generated/hotspots.md`
- `docs/service/generated/health-report.json`

Rules:
- generated artifacts must stay rebuildable;
- mark low confidence explicitly;
- do not present generated output as canon.

## Phase 5: audit contour health

Validate:
- core file presence;
- link integrity;
- dead paths;
- command validity where possible;
- stale gap items;
- startup/canon duplication;
- drift signals;
- oversized canonical docs.

## Phase 6: final response

Return:
1. active mode used;
2. files created;
3. files updated;
4. generated artifacts created or refreshed;
5. triggers detected;
6. gaps introduced or updated;
7. unresolved issues;
8. files explicitly not created and why;
9. promotion or prune actions recommended now.

# Support scripts

The skill must add or maintain these scripts:

- `bin/bootstrap.sh`
- `bin/refresh_contour.sh`
- `bin/audit_contour.sh`
- `bin/promote_learning.sh`
- `bin/prune_contour.sh`

## `bin/bootstrap.sh`

Responsibilities:
- create only the mandatory core and generated layer;
- do not generate event-driven docs;
- do not generate empty optional folders;
- do not create documentation forests.

## `bin/refresh_contour.sh`

Responsibilities:
- rebuild the generated layer from current repo state where possible;
- detect likely triggers;
- propose exact canonical updates;
- recommend event-driven docs only when justified.

It must not create optional layers automatically just because they might help later.

## `bin/audit_contour.sh`

Responsibilities:
- validate contour integrity;
- emit machine-readable failures or warnings;
- fail on missing mandatory files, broken references, expired gaps, or severe drift.

A fake audit script is worse than no audit script.

## `bin/promote_learning.sh`

Responsibilities:
- accept a transient learning input from task summary, review note, incident note, or bugfix summary;
- classify it;
- propose exactly one canonical home or one justified event-driven home;
- reject duplication;
- output promotion candidates without silently mutating canon unless explicitly requested.

## `bin/prune_contour.sh`

Responsibilities:
- identify stale, duplicated, oversized, low-read-path, and mostly-placeholder docs;
- recommend delete / merge / archive;
- default to delete unless there is operational reason to keep history;
- emit machine-readable candidates and reasons.

# SDLC hooks

Without enforcement, the contour will rot.

The repository operating model must include:

## PR expectation

Every non-trivial change should report:
- whether a contour trigger fired;
- if not, why not;
- changed surface summary;
- commands run;
- what was not verified locally;
- risk notes.

## CI expectation

CI should run:
- contour audit;
- generated-layer refresh if supported;
- expiry checks for `knowledge-gaps.yaml`.

## Review expectation

If a trigger fired, the reviewer must verify that the contour was updated or that the omission is explicitly justified.

# Success criteria

This skill succeeds only if all of these are true:

1. a new engineer or agent can quickly find how the service is structured;
2. a new engineer or agent can quickly find how to verify a change;
3. risky areas are visible without reading the whole repo;
4. unresolved durable uncertainty is centralized and time-bounded;
5. generated artifacts support navigation and audit without becoming alternate truth;
6. event-driven docs stay absent unless justified;
7. the contour becomes easier to read after the skill runs, not harder;
8. the repo has a real path to refresh, audit, promote, and prune knowledge over time.
