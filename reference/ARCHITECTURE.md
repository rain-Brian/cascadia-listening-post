# Architecture

The shape of the system, and what maps onto what. The steps are in
[../REBUILD.md](../REBUILD.md); this is the map you read alongside them.

## The shape

```
public feeds
    |
    v
[ capture ]        continuous, long-running, no models
    |
    v
[ object store ]   the system of record
    |
    v
[ inference ]      batch, GPU, leased and torn down
    |
    v
[ report build ]   page generation from run artifacts
    |
    v
[ publish gates ]  rights, then redaction
    |
    v
[ static site ]    public
```

Every arrow crosses a contract. They are in [../contracts/](../contracts/), and they are
Stage 1 because everything else is cheaper once they exist.

## Two boundaries that earn their keep

**Capture never runs a model.** This is what lets the inference tier carry restrictive model
licences without those reaching the capture tier.

**The public site carries no code.** This is what keeps those same licences from gating a share
of the results.

Both are worth copying even if you split the repositories differently.

## Principle 0

**If every LLM agent is switched off, capture, transfer, inference and alerting all still work.**

Agents consume the contract; they never produce into it. Written down and enforced, because the
alternative is a system where a bad generation is a missing recording. See [AGENTS.md](AGENTS.md).

## Capabilities

| Capability | Cloudflare | Azure (reference) |
|---|---|---|
| Media object store | R2 | ADLS Gen2 |
| Static report site | Pages | GitHub Pages |
| Scheduler | Workers Cron Triggers | Automation runbooks |
| Event fan-out | Queues | Event Hubs + Event Grid |
| Report index | D1, optional | a generated JSON file |
| Config and run state | KV / Durable Objects | Key Vault + blob |
| **Capture** | **not supported** | VM + init system |
| **Model inference** | **not supported** | leased GPU batch |

The last two rows are a property of the workload, not a gap in the mapping. Capture is a
long-running transcode; inference is GPU batch with custom weights. See
[../deploy/bring-your-own/](../deploy/bring-your-own/).

## On event-driven ingest

A queue between the object store and inference is the textbook design and it is not where to
start. It must filter to the raw prefix only, or writebacks from inference re-trigger it in a
loop. It needs a real checkpoint store and a dedicated consumer group, or a restart silently
skips the backlog. It needs debouncing per day-prefix.

A scheduled sweep is simpler, resumable, and sufficient for a daily cadence. Build the sweep,
then earn the queue.

## Layer checklist

The nine layers, in dependency order. Layers 1 to 4 cannot be skipped. Each maps to a stage in
[../REBUILD.md](../REBUILD.md).

| Layer | What | Stage |
|---|---|---|
| 1 | Contracts: one path implementation, versioned records, validated on write | 1 |
| 2 | Capture supervision: grace periods, separated budgets, escalation | 3 |
| 3 | Signal health: completed segments, signal statistics not file statistics | 4 |
| 4 | Transfer: spool state, projected disk, structured error parsing | 5 |
| 5 | Orchestration: checkpointed runner, idempotency, lease-based teardown | 6, 10 |
| 6 | Reproducibility: lockfiles, digests, one image per model, recorded seeds | 6 |
| 7 | Credential handling: nothing on the process table, umask before write | 3, 6 |
| 8 | Quality gates: linting, tests, secret scanning, alerts as code | 10 |
| 9 | Licensing and distribution readiness | 0 |

## Where to start

1. **Contracts.** Everything else gets cheaper.
2. **Signal health.** Highest value per unit of work.
3. **Capture supervision.** The "never lose two weeks again" layer.
4. **Credential handling.** Cheap now, unpleasant to retrofit.

Orchestration and event-driven ingest come later. A scheduled sweep produces reports, and
reports are what tell you whether the rest is working.
