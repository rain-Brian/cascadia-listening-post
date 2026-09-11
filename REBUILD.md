# Build instructions

Work through these in order. Each stage says what to do, what to get right, and how to know it
worked.

Read [LIMITATIONS.md](LIMITATIONS.md) first.

Notation: `<angle-brackets>` are values you supply. Nothing here has a default, on purpose.

---

## Stage 0: rights and licences

Do this before capturing a byte. It gates everything and it is the part that cannot be fixed
afterwards.

1. **Pick your feeds.** For each, find the actual licence notice, not a summary of it.
2. **Record the terms** in your feed registry (Stage 1). A feed defaults to
   `redistribute: unknown`, which is unpublishable, and that is correct.
3. **Record what the position rests on** in `verified_by`. Say plainly when it rests on a
   published page rather than a written grant.
4. **Set `commercial_use` to what the holder permits**, not to what you intend to do.
5. **Decide the commercial question for your organisation.** Non-commercial feed terms are safe
   to operate under only if you can commit to non-commercial use. If you cannot, clear it with
   each holder now.
6. **Obtain each model and read its licence.** Copyleft binds the code; responsible-use licences
   can restrict categories of use and follow the outputs.

> Do not set `redistribute: yes` because a feed is publicly viewable. Public and reusable are
> different properties.

**Verify:** every feed in your registry has a `rights` block with a non-empty `verified_by`, and
you can say out loud what each model's licence permits.

Detail: [reference/RIGHTS.md](reference/RIGHTS.md).

---

## Stage 1: contracts

Before provisioning anything. Everything after this is cheaper for having done it.

1. Copy [contracts/](contracts/) into your project.
2. **Write one implementation of lake path construction and parsing.** One, in one language. If
   a second language needs it, give it the same golden fixture file and assert identical results.
3. **Decide the partition question once**: partitioned by date, or a flat sync. Write the answer
   down.
4. Build your registry from [contracts/feeds.example.json](contracts/feeds.example.json).
5. Validate on write, in every producer.

> The reference deployment deferred this. One schema change then cost roughly fourteen edit
> sites across two repositories and three languages, with no test that would catch a missed one,
> and three implementations of the partition builder that disagreed with each other.

**Verify:** round-trip property tests pass (construct, parse, construct again). An off-contract
path is *refused*, not coerced.

```sh
python3 tools/validate_schemas.py
```

---

## Stage 2: object store

1. Create one bucket or container.
2. Lay out the zones per [contracts/lake-path.md](contracts/lake-path.md): `raw`, `sent`,
   `prepared`, `manifests`, `logs`, `inference`.
3. **Set a lifecycle policy on day one:** cool at 30 days, archive at 90, **no delete rule.**
4. **Set a retention lock on `raw/`.** It is the only copy of something that cannot be
   re-recorded.
5. Create scoped credentials. Capture gets write on `raw/` and nothing else. **Capture must not
   be able to delete.**

Cloudflare: [deploy/cloudflare/](deploy/cloudflare/). Azure: [deploy/azure/](deploy/azure/).

**Verify:** write a file at a contract path, read it back, confirm your parser round-trips it.
Confirm the capture credential cannot delete.

---

## Stage 3: capture

One long-running process per feed, under an init system, writing completed segments to `raw`.

**This tier does not run on Workers.** See [deploy/bring-your-own/](deploy/bring-your-own/).

Get these four right now, because retrofitting them is unpleasant:

1. **A start-up grace period before any watchdog may act.** Never restart a process that started
   more recently than the time it needs to produce its first artifact.
2. **Separate the supervision budget from the remediation budget.** If the init system allows N
   restarts per interval and your watchdog also restarts, they exhaust the same budget together
   and the unit stays failed permanently.
3. **Guard the restart call.** Under `set -e`, restarting an already-failed unit exits non-zero
   and aborts the whole watchdog sweep, so every later feed goes unchecked that cycle.
4. **Never let a fetch failure produce a plausible artifact.** If you cannot fetch, write nothing
   and report it. A camera bridge that reuses its last good frame keeps the archive perfectly
   fresh while the camera is dead.

> Points 1 and 2 together cost twenty hours of one feed in the reference deployment. The source
> published a growing playlist that the decoder treated as on-demand, so it needed minutes to
> reach the live edge; the watchdog restarted it at two minutes, forever.

**Verify:** kill a capture process. Confirm it returns, that the event is reported, and that the
watchdog still evaluates every *other* feed in the same sweep. Then let one exhaust its restart
budget and confirm something escalates.

---

## Stage 4: signal health

**Do this before inference.** Highest value per unit of work in the system.

1. Run over **completed** segments only.
2. Emit signal statistics, not file statistics: crest factor, high-to-low frequency ratio, mains
   prominence.
3. Seed thresholds from a period you know was good.
4. Alarm on the dead-channel signature: crest collapse at an unchanged mean level.

> Freshness defined as newest file modification time is a trap. A segmented encoder holds the
> current segment open and appends to it, so the timestamp keeps moving while it writes silence.
> Three real failures in the reference deployment reported healthy throughout.

**Verify:** replay an archived period containing a known failure and assert the check alarms
*before* the date the failure was noticed.

---

## Stage 5: transfer

Skip if capture writes straight to the object store.

1. A spool with explicit state: pending, in flight, done, failed.
2. Backoff.
3. A disk guard alerting on **projected time to full**, not percent used.
4. Parse your transfer tool's *structured* output. String-matching human-readable output means a
   message-format change reads as success.
5. Per-camera attribution in manifests. Never a placeholder like `all`.

**Verify:** fill a scratch volume, confirm the guard alerts before 100%. Kill an upload
mid-transfer, confirm it resumes without duplicating manifest rows.

**Then test the prune path specifically**, because it is usually the only code that deletes data
and usually the only code with no test:

- Nothing is deleted when the sync reports a hard failure.
- Nothing outside the retention window is deleted when it succeeds.
- An unrecognised transfer message fails closed.

---

## Stage 6: inference

Lease compute, run, tear down. **This tier does not run on Workers.**

1. Obtain each model from upstream under its own licence.
2. **Pin everything**: a lockfile, and model revisions by digest rather than a branch.
3. One container image per model. Not three virtual environments assembled by hand.
4. Set and record seeds.
5. Write detections through the contract, validated on write.
6. Idempotency keyed on `(model_name, model_version, source_blob)`.
7. **Resolve each model's concurrency in one place**, and route every call path through it.
8. **Measure throughput on the hardware you will run on** before sizing a sweep. Laptop timings
   do not transfer.
9. **Deploy with provenance.** Refuse to stage a dirty tree or a commit not on main, stamp the
   commit into the deployment, and print it on every run. Compute hosts get their code the same
   way; a hand-copied tree drifts.
10. **Retry compute start on the provider's transient errors**, per host. One host that cannot
    start must not drop the others.
11. **Survive a dropped session.** Keepalives on remote sessions, and poll each run's own status
    artifact. The verdict follows the artifact, not the session.

> A scheduled path bypassed the concurrency helper the manual path used: four jobs of fourteen
> workers each on a sixteen-core host exhausted memory, and both hosts became unreachable.

**Teardown is the expensive part to get wrong:**

- Whatever provisions compute owns destroying it, with a hard time-to-live as a backstop.
- **Teardown must not be a step inside the success path.** Run it on its own schedule.
- Past lease expiry, an idle machine is reclaimed whether or not any reconciliation exists.
- Require *live* evidence of work to hold a machine past expiry. If liveness cannot be read,
  **hold and alert** rather than reclaim.
- If the cloud is unreachable, raise. An empty list looks like success.
- **Teardown after a failure goes through the same guards.** Never stop a machine by name: on
  shared capacity that can stop somebody else's work.

> In the reference deployment teardown lived inside the campaign runner and consulted that
> campaign's reconciliation, so the only code that released a machine was code that does not run
> when a campaign fails. One incident cost $27, the next $133, when a finished sweep left two
> machines running 86 hours past expiry.

**Verify:** run the same input twice with the same idempotency key, confirm no duplicate work.
Build from the lockfile on two clean hosts, confirm identical resolved dependencies and identical
output. Let a lease expire and confirm reclamation without a successful campaign. Drop a remote session
mid-run and confirm the run's verdict still comes from its artifacts.

---

## Stage 7: measure false-positive floors

Before publishing anything as a detection.

1. For each label at each site, run windows where the label **should not** appear.
2. The rate at which the model fires anyway is the floor for that label at that site.
3. Store floors with the date measured.
4. **A label with no measured floor gets no card**, however confident the model was.
5. **Never pool floors across sites.**
6. **Test separability, not only position.** A rate that cannot be told apart from the floor
   licenses nothing.
7. **Screen known contaminants before counting.** Keep a registry per site with the measurement
   that identified each one, run the screen as a required step, and state on every report at that
   site what was done about each.

> Pooling lets a busy site clear a threshold on its own volume and then license claims at a quiet
> site that never earned one. Both of these rules exist because the reference deployment broke
> them and had to correct published pages.

If that leaves nothing publishable, publish a queue instead, plainly marked. Do not lower a
threshold to produce a result.

**Verify:** take a label you know is absent from a site and confirm the pipeline refuses to show
it at high confidence.

Detail: [reference/METHODS.md](reference/METHODS.md).

---

## Stage 8: reports and publishing

```
build  ->  rights gate  ->  redaction gate  ->  quality gate  ->  index  ->  restyle  ->  verify site
```

The gates run over the **finished bundle in a temporary directory**. A refused publish leaves
nothing behind.

1. **Build each report with the builder for its kind**, from run artifacts. A builder that only
   accounts for runs is not a detection builder.
2. **Make every screening step a builder depends on mandatory**, and fail the report when it
   fails. A skipped optional screen counts everything as clean and still prints its tiles.
3. **Emit a stable card identifier from every page builder**, from the first one.
4. **Choose evidence across the window**: the strongest card from each day first, then the best
   of the rest. Nothing is promoted over a stronger card except to give a day its first card.
5. **Say what did not run.** If a model in the chain did not run, the page says so ("ecotype not
   assessed") and ranks by the model that did.
6. **Compute the licence.** Most restrictive of any contributing feed. Never a site-wide default.
7. **Compute the coverage** from run artifacts, never typed, in the source's own unit: hours for
   audio, frames for stills, clips for video. Hours for video only from recorded clip durations.
8. **Resolve model names through one registry**, and fill licence, lineage and caveat from it.
   Record the full code commit, or null.
9. **Rights gate**: refuse any feed whose `redistribute` is not `yes`. No override flag.
10. **Redaction gate**: content scan for infrastructure detail. Overrides take a specific literal
    string, never a rule, and every use is recorded in the published artifact.
11. Verify every local reference resolves *inside* the bundle, and refuse if any does not. The
    one exception is the site's shared stylesheet, which the site owns and checks.
12. **Quality gate**: a recognised review status; a positive count in the manifest with a
    definition of what it counts; evidence on the page or a stated waiver; every known contaminant
    at the declared sites addressed by name; declared sites matching per-camera counts; numeric
    confidences.
13. Publish, then regenerate the index, then restyle, then verify the whole site. In that order.
    Restyle is not optional. A failing verify stops the change from being proposed.
14. **Stage every file that sequence writes**, from one named list tested against what the steps
    produce, and stop. A person pushes.

> One report in the reference deployment published a station rate of 21.8% where the model's own
> verdict gave 15.34%, which put the station inside its measured floor's interval rather than
> above it. The figure existed only in the page's prose, so nothing could check it.

> Retrofitting the card identifier is what currently blocks the reference deployment's review
> backlog: only one of several builders emits it, so pages from the others cannot be published as
> reviewed even though the review layer, verdict parser and export path all exist.

Test real builder output through the real gates. The scheduled path's tests stubbed the builder
and the publish step, and two refusals surfaced only when real output first went through them.

To correct a report that is already public, retire it; do not edit it. See
[reference/PUBLISHING.md](reference/PUBLISHING.md#correcting-a-public-report).

```sh
python3 tools/check_redaction.py <bundle-dir>
```

**Verify:** publish a report built from a feed marked `redistribute: no` and confirm refusal. Put
a hostname in a page caption and confirm refusal. Publish a detection report with no
`positive_definition` and confirm refusal. All three must fail closed.

Detail: [reference/PUBLISHING.md](reference/PUBLISHING.md).

---

## Stage 9: the site

The easy part. Plain files: no build step, no framework, no runtime, no environment variables.

Two host requirements, and only two:

1. Serve `.json`, `.mp3` and `.mp4` with correct content types.
2. Do not run a static-site generator over already-rendered HTML.

Cloudflare Pages: [deploy/cloudflare/](deploy/cloudflare/#5-the-report-site-on-pages).

Keep the site repository generated, and say so inside it, or somebody will send a pull request
that the next publish silently overwrites.

What the generator must get right:

1. **Order reports by when their data is from**, not when they were published. Take the period
   from the manifest window; failing that, a date in the title, series name or id; failing that,
   the publish date. Record which, and mark anything not from the window as inferred. An end
   stamped at midnight is exclusive.
2. **Use absolute dates in headings.** "This week" is wrong tomorrow, and fails the regeneration
   check with it.
3. **Put a shared nav on every page**, stamped by restyle so it reaches pages whose builder is
   gone. Write every link relative to the page's own depth.
4. **Disclose the AI tooling on every page.** A shared link lands a reader on a report, not the
   methods page.
5. **No bare detection count on a list row.** Report families count positives differently, and
   a count means nothing without its definition beside it.
6. **One set of totalling rules wherever a total appears**: days as a union, and a report wholly
   inside another over the same sites counted once.
7. Join site labels with a separator that cannot occur inside a label.

> Every report link on the reference deployment's source hub pages returned 404: the hubs sit one
> level down and rendered cards whose URLs were written relative to the site root.

**Verify:** clone the site repository to a clean machine, serve it statically, confirm every
image, clip and stylesheet loads. Then run a site verifier: the quality gate over every report, a
full regeneration diffed against the repository (with generated timestamps normalised in both the
JSON and the rendered HTML), internal links, the disclosure on every page, and reserved hub names.
Run restyle twice; the second run changes nothing.

---

## Stage 10: orchestration

Only now, and start with the simple version.

1. **A scheduled sweep over a date range.** Resumable, which an event-driven path is not until
   you have built checkpointing properly.
2. Lag the sweep behind the capture day. Reading the day that just ended catches a partial upload
   and records a coverage gap that never existed.
3. Record "no source data" as a distinct outcome from success and failure. A scheduler should
   retry it, not mark the day done.
4. Checkpoint atomically (temp file plus rename), flush in a `finally`, and make checkpoint
   corruption fail loudly.
5. A status field that can express failure. If the only value it ever takes is `ok`, it is not a
   status.
6. **Record intent before anything else.** One ledger entry per scheduled unit (a source-day,
   say), written before any gate runs: `expected`, `running`, `complete`, `failed` or `deferred`,
   the time it fell due kept across updates, an attempt count, atomic writes.
7. **Watch the inference tier, not only capture.** A unit that was due and never ran, or failed
   and was not retried, is loud but does not stop today's run, which is how the backlog shrinks.
8. **A rehearsal runs every gate**; only the actions are guarded. It writes a rehearsal ledger,
   never the production one.
9. **Unreachable is not empty.** A cloud query that fails must not read as "nothing running".
   When the run is live, hold.
10. **A check for other busy work excludes its own process group**, or the scheduled run holds on
    itself.
11. **Capture a command's exit status directly.** A compound statement's status is not its
    command's, and under `set -e` a clean check that exits non-zero (`grep -c` finding nothing)
    kills the run.
12. **Discover the staged file list** rather than writing it by hand, and verify the deployment
    from the directory the scheduler will run it in.
13. A lock records its holder and reclaims a dead one.
14. **Survive host sleep** by polling artifacts, and schedule for when the host is awake.
15. Run health checks in gating mode, so the scheduler records a failure as a failure.

> On one date every campaign failed at dispatch and eighteen job-days went unprocessed while every
> existing rule reported healthy, because every rule watched capture. A rehearsal that skipped the
> gates hid a clean health check that would have aborted every live run; another wrote "complete"
> into the production ledger for a day that never ran.

**Alerts as code**, and split per service:

> A rule aggregating every service into one condition fires once, stays fired while any one
> service is down, and deduplicates every subsequent failure of every other service. In the
> reference deployment one stuck alert made the whole alerting layer inert for fourteen days.

Add a rule that fires when any alert instance has been active beyond a threshold. That is the
dead man for the dead man.

**Verify:** stop the health collector and confirm a dead-man alert fires. Take one service down,
then a second, and confirm the second produces its own notification. Run a rehearsal and confirm
every gate executed and the production ledger is unchanged. Then watch one live run end to end
before enabling the schedule.

> The reference deployment's first live scheduled run took 15h20m, completed four of six
> source-days, and found defects in the seams between components that no test reached.

---

## Stage 11: advisory agents

Optional, and last.

**Principle 0: if every LLM agent is switched off, capture, transfer, inference and alerting all
still work.**

1. Split every agent into a deterministic half that computes findings and a model half that
   explains them.
2. **Enforce the boundary in the harness, not the prompt.** Invoke the model with no tools
   enabled.
3. Degrade to printing the raw deterministic findings when the model is unavailable.
4. No prompt may mark a run complete, release compute, override a gate, or publish.

**Verify:** disable the model entirely and confirm every pipeline stage still runs.

Detail: [reference/AGENTS.md](reference/AGENTS.md).

---

## The failure mode to watch for throughout

Across four separate incidents in the reference deployment, the same thing happened: **the fix
existed and was not in the path that executes.** Merged to main but not deployed to the running
copy. Scheduled in the cloud but disabled. Built and tested but left in an unmerged branch.
Merged and deployed, but the compute hosts ran a hand-copied tree without it.

Building it is not shipping it. Check what is actually running.
