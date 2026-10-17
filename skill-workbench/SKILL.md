---
name: skill-workbench
description: Create and improve agent skills by resolving consequential requirements, defining acceptance examples, running evaluations, and adding an evidence-based debug mode. Use when a user wants a working, testable skill or needs to diagnose a skill's failures; not for ordinary execution of an unrelated skill.
---

# Skill Workbench

Turn the user's workflow into a skill whose behavior can be tested and explained from artifacts. Write user-facing material in the user's language.

## 1. Establish the contract

Read the current request, prior decisions, and existing skill if supplied. Reuse answers already given. For an existing skill, inspect a reported failure before proposing a rewrite.

Capture a short brief outside the target skill:
- task, intended users, activation examples and exclusions;
- input and output contracts, missing-data behavior;
- observable success criteria and unacceptable outcomes;
- permitted actions and consequential decisions still unresolved.

Distinguish user requirements, source facts, and your proposals. Ask only questions whose answers materially change correctness, scope, or the consequences of an error. Batch a few focused questions with suggested defaults; do not run an exhaustive interview. Decide routine wording, file layout, and implementation yourself. Explicit user delegation allows you to choose policy; record it as delegated, not as a supplied requirement.

Delegation of routine implementation is not delegation of interpretation rules. Rules that change which records qualify, who owns an action, or how an ambiguous deadline becomes a date affect the result. If the user has not specified or explicitly delegated them, ask a focused question before finalizing that behavior. Do not call a plausible convention a technical detail.

If a consequential criterion is unknown, ask and continue independent preparation. Do not silently convert an assumption into a business rule. A blocked draft is useful; a falsely finished skill is not.

## 2. Define examples before implementation

Use [the eval procedure](references/evals.md). An eval is an input plus observable expectations fixed before execution, not a second prompt asking whether the first answer is good.

For a new skill, start with a normal case, a missing/invalid-input case, and a boundary case when relevant. Include activation and non-activation examples. User-provided examples are preferable; mark invented examples as synthetic and expectations as author-generated. Reserve fresh cases for subsequent evaluation. For a narrow fix, the reproducer and relevant regression cases may suffice.

Keep evaluator expectations separate from executor inputs. Do not add example-specific exceptions simply to match a label. Resolve disagreements between the written rule and the expectation explicitly.

## 3. Build or improve the skill

Use the host's skill-creator for packaging if available; this skill must also work without it. Do not recursively invoke this workflow on itself. Preserve the requested location and existing invocation policy.

- Keep `SKILL.md` focused on decisions the model would otherwise get wrong. Put substantial conditional details in linked references.
- Define structured boundaries where they help integration or checking. Do not force every prose task into JSON.
- Use a finite vocabulary for operational decisions when the consumer needs one; define each value and missing-input behavior. Keep evidence and explanation alongside the status.
- Put repeatable deterministic work in scripts when that removes actual model work: parsing, schema checks, exact comparisons, aggregation. Do not replace semantic judgment with brittle regexes or add scripts solely to satisfy a checklist.
- Include a documented normal invocation and `debug=true` invocation. Implement debug behavior using [the debug contract](references/debug.md). Debug is an instruction-level convention unless an actual runner implements a flag; do not pretend the host supplies a universal debug switch.
- Keep debug data and eval artifacts outside the installed skill. Never change the underlying task's outcome or grant extra external permissions because debug is enabled.

For existing skills, preserve a baseline and make the smallest change supported by observed failure. Avoid unrelated rewrites and new universal restrictions.

## 4. Execute and inspect

Run available packaging validation and meaningful checks for scripts. Then execute representative behavioral cases with the target model/runtime, not only a format validator. If subagents are available and authorized, use fresh-context executors with only the skill, realistic request, and allowed raw inputs. Keep their outputs separate from the source. Otherwise run in the current context and state that limitation.

Test the generated skill in normal and debug modes on the same representative input. Compare task-relevant outputs, not exact wording; check whether debug artifacts identify applied criteria, evidence, assumptions, and checks. Do not request hidden chain-of-thought.

Inspect failures before editing: was the cause the input, specification, implementation, tools, model behavior, or expectation? Preserve first responses. After a change, rerun the affected cases and relevant regressions. Use new cases when claiming an independent check; passing only tuned examples is insufficient. Stop once the agreed acceptance conditions pass; do not invent endless gates. If blocked, report the blocker and unrun checks rather than fabricate a pass.

## 5. Deliver a usable result

Return the skill location, a normal and debug usage example, what actually ran, observed mismatches, and remaining limits. Separate mechanical validity from behavioral quality. State which model and context were used when known; do not guess configuration, call counts, costs, or latency.

In this workflow's own `debug=true` mode, save a sanitized request, the brief, a snapshot of the candidate skill, eval inputs and frozen expectations, first outputs, tool/check results, and a concise decision report in a fresh run directory. Follow the same [debug contract](references/debug.md). Record why consequential choices were made using supplied requirements and observable evidence. If file/tool execution is unavailable, provide the draft and clearly label tests `NOT_RUN`; do not claim artifacts were saved.
