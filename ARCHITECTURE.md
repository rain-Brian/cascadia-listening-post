# Architecture

The system as capabilities, so you can map it onto whatever you are building on.

This describes the target design, not a snapshot of any running deployment. Where the
reference deployment falls short of it, [LIMITATIONS.md](LIMITATIONS.md) says so.

## Principle 0

**If every LLM agent is switched off, capture, transfer, inference and alerting all still
work.**

LLM agents consume the contract. They never produce into it. This is written down and enforced
rather than assumed, because the failure mode it prevents is a system that cannot be reasoned
about: one where a language model sits on the data path and a bad generation becomes a missing
recording. See [AGENTS.md](AGENTS.md).

## The shape

```
public feeds
    |
    v
[ capture ]  continuous, long-running, no models
    |
    v
[ object store ]  the system of record
    |
    v
[ inference ]  batch, GPU, leased and torn down
    |
    v
[ report build ]  page generation from run artifacts
    |
    v
[ publish gates ]  rights, then redaction
    |
    v
[ static site ]  public
```

Every arrow crosses a contract, and the contracts are in [contracts/](contracts/). That is the
part worth getting right first: the reference deployment shipped without them and paid for it
with roughly fourteen edit sites across two repositories and three languages for a single
schema change, with no test that would catch a missed one.

## Capabilities and how they map

| Capability | Cloudflare | Azure (reference) | Notes |
|---|---|---|---|
| Media object store | R2 | ADLS Gen2 | The system of record |
| Static report site | Pages | GitHub Pages | Plain files, no build step |
| Scheduler | Workers Cron Triggers | Automation runbooks | Fires campaigns |
| Event fan-out | Queues | Event Hubs + Event Grid | Optional, see below |
| Report index | D1 | A generated JSON file | A file is genuinely enough |
| Config and run state | KV / Durable Objects | Key Vault + blob | Secrets need a real vault |
| Capture | **not supported** | VM + init system | Long-running transcode |
| Model inference | **not supported** | Leased GPU batch | Custom weights |

The last two rows are not a gap in the mapping, they are a property of the workload. See
[deploy/bring-your-own/](deploy/bring-your-own/).

**On event-driven ingest.** A queue between the object store and inference is the textbook
design and it is worth building eventually, but it is not where to start. It has to filter to
the raw prefix only, or writebacks from inference re-trigger it in a loop; it needs a real
checkpoint store and a dedicated consumer group, or a restart silently skips the backlog; and
it needs debouncing per day-prefix. A scheduled sweep over a date range is simpler, resumable,
and sufficient for a daily cadence. Build the sweep, then earn the queue.

## The layers

Nine layers, ordered by what depends on what. Layers 1 through 4 are the ones you cannot skip.

### Layer 1: contracts (the keystone)

A small shared package plus JSON Schemas, vendored into every repository that reads or writes
the lake. Build this first. Everything else is cheaper afterwards.

- **One implementation of path construction and parsing.** Not two, and definitely not four in
  three languages. See [contracts/lake-path.md](contracts/lake-path.md).
- **Versioned records** carrying `schema_version`, `run_id`, `source_timestamp_utc`,
  `model_name`, `model_version`, `code_commit` on every row.
- **A common detection envelope** with the payload discriminated by model kind, so an acoustic
  detection and a video detection share an outer shape.
- **Validated on write**, with round-trip tests in continuous integration.

Decide the partition question once, at the start: either the uploader partitions by date or the
contract is a flat sync. In the reference deployment these disagreed silently for months, and a
job parsing dates out of flat paths wrote every result to a partition literally named `raw`,
with no validation and no error.

### Layer 2: capture supervision

Capture is a long-running process that will fail, and the interesting part is what happens
next.

- **Separate the supervision budget from the remediation budget.** If your init system allows
  N restarts per interval and your watchdog also issues restarts, they consume the same budget
  and exhaust it together. Then the unit sits failed permanently and nothing re-arms it.
- **A start-up grace period.** Never restart a process that started more recently than the time
  it plausibly needs to produce its first artifact. Without this, any slow-starting capture is
  unrecoverable by construction: it is killed and restarted before it can ever reach the live
  edge, forever.
- **Track restart effectiveness.** If N restarts produce no change in artifact age, the restart
  is not the remedy. Escalate instead of repeating.
- **Distinguish "never produced" from "stopped producing".** They are different failures with
  different fixes and they must not take the same action.
- **A failed unit is the most important thing to report, not a reason to stop looking.** A
  watchdog that returns early for anything not currently running goes permanently silent about
  exactly the units that need attention.
- **Heartbeat on every run, healthy or not.** A watchdog that emits only on the failure path
  produces silence when healthy, which is indistinguishable from the watchdog not running. The
  heartbeat is what makes a dead-man alert possible.

### Layer 3: signal health

**The highest value per unit of work in the whole system.** Liveness and health are different
questions, and measuring the first while believing you measured the second is how a feed
records nothing for weeks while every check reports green.

Freshness defined as "newest file modification time" is a trap. A segmented encoder holds the
current segment open and appends to it, so the timestamp keeps moving while the encoder writes
silence. That is "is a file handle moving", not "did a complete segment land".

Run over **completed** segments only, and emit signal statistics rather than file statistics:
crest factor, high-to-low frequency ratio, mains hum prominence. A dead audio channel has a
recognisable signature, typically a crest factor collapse at an unchanged mean level. For fixed
cameras, the equivalent failure is a bridge that reuses its last good frame when a fetch fails,
which keeps the archive perfectly fresh while the camera is dead.

Three real failures in the reference deployment reported healthy throughout, and this layer
would have caught all three.

### Layer 4: transfer

- A spool with explicit state (pending, in flight, done, failed), backoff, and a disk guard
  that alerts on **projected time to full** rather than percent used.
- Parse your transfer tool's structured output. String-matching human-readable output means a
  message-format change reads as success.
- Per-item attribution in manifests. A manifest that hardcodes the source to `all` cannot tell
  you which camera failed.
- One authentication path, with any fallback explicit and alarmed. Never swallow an
  authentication failure.

**Test the destructive paths specifically.** Pruning is usually the only code in the system
that deletes data, and it is usually gated on a heuristic. Assert the ordering invariant (the
sync succeeds before anything is deleted), assert the retention window, and assert that an
unrecognised transfer message fails closed rather than reading as success.

### Layer 5: orchestration

- A runner with checkpointing, a process pool, and per-item failure isolation. Write checkpoints
  atomically (temp file plus rename), flush in a `finally`, and make checkpoint corruption fail
  loudly rather than silently reprocess a range.
- A status column that can express failure. If the only value it ever takes is `ok`, it is not
  a status column.
- Idempotency keyed on `(model_name, model_version, source_blob)`, so a re-run produces no
  duplicate work.
- **Whatever provisions compute must own destroying it, with a hard time-to-live as a
  backstop.** Make the lease the contract: past expiry, an idle machine is reclaimed whether or
  not anything succeeded.

That last point is not theoretical. In the reference deployment, teardown ran as a step inside
the campaign runner and consulted that campaign's reconciliation, so the only path that
reclaimed a machine was the path that does not execute when a campaign fails. A finished sweep
left two machines running 86 hours past an expired lease. Teardown must not be coupled to
campaign success.

### Layer 6: reproducibility

Pin with `==` and a lockfile. Pin model revisions by digest, never a moving branch. Verify
checksums on download rather than recording them afterwards. One container image per model,
built in continuous integration, rather than several virtual environments assembled by hand.
Set and record seeds. Remove hardcoded operator home paths, which block unattended execution.

### Layer 7: credential handling

**Keep every secret off the process table.** A long-running process with a credential in its
argument vector exposes it to any local user for the life of the process. Pass secrets through
environment variables that the tool reads directly, a configuration file, or standard input,
never as a command-line argument. This applies to stream keys, storage keys, shared access
signatures embedded in URLs, and bearer tokens alike.

Set a restrictive umask before writing any rendered configuration, not after. Writing files and
then tightening permissions leaves a window. Write to a temporary file and rename atomically,
so a vault failure mid-run cannot truncate a working config.

Grant the capture user only the specific verbs it needs. Blanket passwordless privilege
escalation collapses the very file-permission boundary the restrictive modes rely on.

Add a content-based secret scanner to continuous integration. Filename-based checks that run
only when a human invokes them are not a gate.

### Layer 8: quality gates

Linting for shell and Python, type checking on the contracts package, tests, schema round-trip
tests, and a secret scan. Alerts defined as code in `deploy/`, not as prose in a document that
can contradict itself.

**One alerting failure is worth designing against explicitly.** If a rule aggregates every
service into a single condition, the first service to fail holds that condition open, and the
alerting system deduplicates every subsequent failure of every other service. The alerting is
not missing, it is inert, and nothing monitors for that. Split rules per service so each gets
its own instance, and add a rule that fires when any instance has been active beyond a
threshold. That is the dead man for the dead man.

### Layer 9: licensing and distribution readiness

This gates handover rather than following it. See [RIGHTS.md](RIGHTS.md) and
[LIMITATIONS.md](LIMITATIONS.md). Settle the model licence positions before a distribution
question arrives, not during one.

## Where to start

If you build these four things in this order, you have a system that can be reasoned about:

1. **Contracts** (Layer 1). Everything else gets cheaper.
2. **Signal health** (Layer 3). Highest value per unit of work.
3. **Capture supervision** (Layer 2). The "never lose two weeks again" layer.
4. **Credential handling** (Layer 7). Cheap, and unpleasant to retrofit.

Orchestration and event-driven ingest come later. A scheduled sweep is enough to produce
reports, and reports are what tell you whether any of the rest is working.
