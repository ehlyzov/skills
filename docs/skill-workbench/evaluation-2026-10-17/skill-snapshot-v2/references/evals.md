# Small, useful evals

## Prepare

Before executing a case, record its ID, realistic request, raw input, expected properties, and the source of those expectations (user, policy, or author proposal). Define success in terms of behavior, not preferred phrasing. For open-ended work, use a short rubric with concrete anchors and examples; avoid pretending one exact answer is required.

Separate executor inputs from evaluator notes. Keep a snapshot or content hashes of the skill and expectations. Record execution model/runtime when available, context (fresh or shared), and attempts. Do not call instruction-only separation a security sandbox.

Example for a meeting action extractor:
- Input: “Ира: пришлю макет к пятнице. Надо ещё проверить метрики.”
- Expected: two explicit actions; Ira belongs only to the first; no owner or deadline invented for the second; preserve “к пятнице” unless a reference date was provided.
- Missing-input case: no transcript; ask for it instead of returning “no actions”.
- Boundary: “Может быть, когда-нибудь перепишем сервис” is not a committed action under a policy requiring explicit commitments. That policy must come from the brief or be labeled as a proposal.

These are illustrative examples, not mandatory policy for other skills.

## Run and grade

Send the executor only the skill, request, and necessary raw artifacts. Save the first response and tool failures before any retry. Use a new run directory for a retry or revision. If only the author can execute, label the run as author-context, not independent.

Check deterministic properties in code when useful. Evaluate semantics against the frozen criteria separately. A model judge may assist but is not automatically ground truth. For each case use:
- `PASS`: recorded execution satisfies the stated criteria;
- `FAIL`: recorded execution violates at least one criterion;
- `BLOCKED`: an attempted execution could not complete due to a documented dependency;
- `NOT_RUN`: no execution took place.

If a label conflicts with the written criterion, keep the original label and document the disagreement. Resolve the policy with its owner when necessary, then version expectations rather than rewriting the past result.

For debug testing, compare a normal and debug execution on the same input. Require the same task-relevant decisions while allowing different wording. Debug evidence must support the result without introducing additional actions or invented facts.

Activation testing is separate from forced invocation. If selection cannot be tested in the host, state `NOT_RUN`; a good description alone does not demonstrate correct routing.

## Report honestly

Report counts with denominators, excluded/blocked cases, model configuration, whether expectations were human-provided or generated, and whether inputs are synthetic. A small one-model sample demonstrates observed behavior, not universal reliability. Comparing before/after on the same cases is useful for regressions; fresh cases are needed to assess whether a fix generalizes.
