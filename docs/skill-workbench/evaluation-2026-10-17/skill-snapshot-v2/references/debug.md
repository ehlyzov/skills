# Debug contract

`debug=true` asks the executing agent to save observable evidence alongside its normal result. It is not a built-in platform flag. Document how the target skill receives it (request text, config, or a real CLI option) and where artifacts are written. Both this workbench and the skills it produces support the convention.

Use a fresh directory per run, outside the installed skill. Keep:
- the input or a sanitized copy with omissions identified;
- the skill version/snapshot and relevant runtime configuration when known;
- the actual output, including a partial output on failure;
- commands/tool outcomes and validation results relevant to the decision;
- `debug.json` with concise decision explanations in the format below.

Store only what is needed to reproduce or diagnose the issue. Do not dump credentials, unrelated conversation history, private reasoning, or unrestricted tool output. Record redaction and its impact on reproducibility. Do not upload debug artifacts unless publication is within the user's scope.

```json
{
  "status": "PASS",
  "summary": "The agreed checks passed on the recorded example.",
  "artifacts": ["input.json", "output.json", "checks.json"],
  "decisions": [
    {
      "decision": "Leave owner unspecified",
      "basis": "The user requires explicit assignment; the transcript supplies none.",
      "evidence": ["input.json"],
      "assumptions": []
    }
  ],
  "checks": [
    {
      "name": "Output schema",
      "status": "PASS",
      "detail": "Validator exited 0; this checks structure, not interpretation.",
      "evidence": ["checks.json"]
    }
  ],
  "limitations": []
}
```

Fields are required; no extra fields. Status vocabulary: `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`. The top-level status describes the declared scope of the run, not universal skill quality. A required failing check prevents overall PASS. A required blocked or unrun check also prevents overall PASS. Record optional unavailable checks as limitations, outside the required `checks` list.

Paths in `artifacts` are unique, relative to the run directory, and must exist there. Decision/check evidence refers to listed artifacts. Use nonempty concise explanations; do not expose a hidden reasoning transcript. Empty evidence is allowed only when there is no executed check or evidence to cite; explain the limitation. Separate assumptions from supplied facts. For absent data, cite the available input and explain the limitation rather than inventing a quote.

The helper checks report structure, status consistency, and referenced files:

```sh
python3 <skill-workbench>/scripts/check_debug.py <run-directory>/debug.json
```

It does not validate the truth of explanations, all content inside artifacts, or whether a model secretly changed its answer. It prints JSON and returns 0 for a valid report, 1 for errors. Report validity and the run's PASS/FAIL status are distinct.

If the target environment cannot save files, return the ordinary result and a concise debug explanation with that limitation; do not fabricate file paths. Do not require a filesystem-specific report format in that environment.
