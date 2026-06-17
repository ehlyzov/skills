# Pressure Scenario: Full PRD Gate

## User prompt

`Сделай полный PRD по новой фиче: overview, сценарии, implementation plan, hardening plan и stakeholder PDF.`

## Prior risk

Adding a lightweight quick-plan mode could accidentally weaken the full PRD governance path and let the agent start writing scenarios or plans before product decisions are confirmed.

## Expected new behavior

Choose `full-prd`. Run discovery, present Phase 0 scope and decision gate, and wait for user confirmation or explicit delegation before writing scenarios, implementation plan, hardening plan, or PDF.
