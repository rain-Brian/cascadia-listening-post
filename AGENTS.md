# Agents

Where LLM agents fit, and the boundary that keeps them useful.

## Principle 0

**If every LLM agent is switched off, capture, transfer, inference and alerting all still
work.**

Write this down and enforce it. LLM agents consume the contract; they never produce into it.

The rule exists because the alternative is a system nobody can reason about. If a language
model sits on the data path, then a bad generation is a missing recording, and no amount of
prompt care fixes the class of problem. Keeping agents advisory means their worst failure is a
bad suggestion.

## Two tiers

### Tier 1: deterministic workers

These carry the data. No language model anywhere near them.

| Worker | Job |
|---|---|
| capture supervisor | Owns restart budget and backoff; reports exhaustion instead of dying silently |
| signal health | Reads completed segments, emits signal statistics, catches dead channels |
| transfer | Spool state machine, backoff, disk projection, per-camera attribution |
| manifest | Sole writer of the contract; validates before write |
| dispatch | Queue to job: filtered, checkpointed, deduplicated |
| runner | Executes a model over a range with per-item failure isolation |
| reconciler | Decides what actually completed |
| reaper | Reclaims compute on lease expiry |
| heartbeat | Liveness for everything else; the dead-man source |

### Tier 2: advisory LLM agents

These read artifacts the workers produced and draft explanations, review notes or
recommendations.

| Agent | Job | Boundary |
|---|---|---|
| `ops` | On alert, gather evidence and draft the escalation | Drafts only; never executes |
| `triage` | Rank detections for review by model disagreement; draft the run narrative | Reads outputs, writes a report; never gates ingest |
| `drift` | Weekly: diff run metadata, flag model and dependency drift | Advisory |

**No prompt is allowed to mark a run complete, deallocate compute, override a rights or
redaction failure, or publish a report.**

## Enforce the boundary in the harness, not the prompt

This is the part that matters. A prompt saying "you never execute" is a wish. The reference
implementation pipes evidence to a model invocation with **no tools enabled at all**, so the
boundary is a property of the call rather than a property of the text:

```
printf '%s\n\n---\n\nEvidence bundle:\n\n%s\n' "$(cat prompt.md)" "$bundle" \
  | <model-cli> --print --allowed-tools ''
```

It degrades to printing the raw deterministic findings if the model is unavailable or the call
fails. That is the right failure mode: the evidence was already computed by a deterministic
step, so losing the agent loses the summary, not the signal.

## Split evidence from interpretation

Every advisory agent should be two halves:

1. A deterministic step that computes the findings and writes them to a file.
2. A model call that classifies, ranks or explains those findings.

Half one is testable and is the thing you actually depend on. Half two is replaceable and can
be switched off. If you cannot draw that line for a given agent, it is not ready to build.

## Writing the prompts

Four things the reference prompts do that are worth copying:

**Say what the agent may not conclude, in terms of the deterministic artifact.** Not "be
careful" but "do not claim compute should be released unless a deterministic reaper plan marks
it for release; do not claim a campaign is complete unless reconciliation reports it safe to
tear down".

**Encode known failure modes as named cautions.** One prompt carries the memory of a specific
miss: a bear pair hidden by static-object suppression on a particular date, and therefore an
instruction not to treat a static-object flag as proof that nothing moved. That is a regression
guard in prose, and it is worth as much as one in code.

**Ask for a bounded output with a fixed structure.** Under 400 words, grouped as `must fix
before automation`, `can automate around temporarily`, `monitor only`, each naming the artifact
or test that would prove the concern resolved. An unbounded "analyse this" produces prose
nobody reads.

**Lead with the current risk, then next actions in priority order, and say what a missing
piece of evidence would leave blind.** An agent that cannot say what it does not know is worse
than no agent.

## What agents are genuinely good at here

Ranking a review queue by model disagreement, which is a real signal: one model confident while
another is not is exactly where human attention pays. Drafting the narrative for a run so a
person edits rather than composes. Reading across syslog, manifests and health artifacts at
three in the morning to draft an escalation a person then sends.

What they are not for: deciding whether something is publishable. That is rights, redaction,
coverage and floors, and all four are deterministic gates for good reasons.
