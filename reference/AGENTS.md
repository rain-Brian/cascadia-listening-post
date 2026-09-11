# Advisory agents

Reference for Stage 11 of [../REBUILD.md](../REBUILD.md). Optional, and last.

## Principle 0

**If every LLM agent is switched off, capture, transfer, inference and alerting all still work.**

Agents consume the contract; they never produce into it. The rule exists because the alternative
is a system nobody can reason about: if a model sits on the data path, a bad generation is a
missing recording, and no amount of prompt care fixes that class of problem. Advisory agents fail
by giving bad advice.

## Tier 1: deterministic workers

These carry the data. No language model anywhere near them.

| Worker | Job |
|---|---|
| capture supervisor | owns restart budget and backoff; reports exhaustion |
| signal health | reads completed segments, catches dead channels |
| transfer | spool state machine, backoff, disk projection |
| manifest | sole writer of the contract; validates before write |
| dispatch | queue to job: filtered, checkpointed, deduplicated |
| runner | executes a model over a range with per-item failure isolation |
| reconciler | decides what actually completed |
| reaper | reclaims compute on lease expiry |
| heartbeat | liveness for everything else; the dead-man source |

## Tier 2: advisory agents

| Agent | Job | Boundary |
|---|---|---|
| `ops` | on alert, gather evidence and draft the escalation | drafts only, never executes |
| `triage` | rank detections for review by model disagreement | never gates ingest |
| `drift` | weekly: diff run metadata, flag model and dependency drift | advisory |

**No prompt may mark a run complete, release compute, override a gate, or publish.**

## Enforce the boundary in the harness

A prompt saying "you never execute" is a wish. Invoke the model with **no tools enabled**, so the
boundary is a property of the call rather than of the text:

```sh
printf '%s\n\n---\n\nEvidence bundle:\n\n%s\n' "$(cat prompt.md)" "$bundle" \
  | <model-cli> --print --allowed-tools ''
```

Degrade to printing the raw deterministic findings when the model is unavailable. That is the
right failure mode: the evidence was already computed by a deterministic step, so losing the
agent loses the summary, not the signal.

A hook on an agent's tools sees that agent's actions and nothing else. It cannot see a scheduled
job, so an unattended runner calls the same preflight itself.

## Split evidence from interpretation

Every agent is two halves:

1. A deterministic step that computes findings and writes them to a file.
2. A model call that classifies, ranks or explains those findings.

Half one is testable and is what you depend on. Half two is replaceable and can be switched off.
If you cannot draw that line for an agent, it is not ready to build.

## Writing prompts

- **Say what the agent may not conclude, in terms of a deterministic artifact.** Not "be careful"
  but "do not claim compute should be released unless a reaper plan marks it for release".
- **Encode known failure modes as named cautions.** One reference prompt carries a specific miss:
  a bear pair hidden by static-object suppression on a given date, and therefore an instruction
  not to treat a static-object flag as proof that nothing moved. A regression guard in prose.
- **Ask for bounded output with fixed structure.** Under 400 words, grouped as `must fix before
  automation`, `can automate around temporarily`, `monitor only`, each naming the artifact that
  would prove the concern resolved.
- **Lead with current risk, then actions in priority order, and say what missing evidence leaves
  blind.** An agent that cannot say what it does not know is worse than no agent.

## What agents are good at here

Ranking a review queue by model disagreement, which is a real signal: one model confident while
another is not is where human attention pays. Drafting a run narrative so a person edits rather
than composes. Reading across logs, manifests and health artifacts to draft an escalation.

What they are not for: deciding whether something is publishable. That is rights, redaction,
coverage and floors, and all four are deterministic gates for good reasons.
