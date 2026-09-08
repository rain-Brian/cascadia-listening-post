# Cloudflare: a worked example

Stages 2, 9 and 10 of [../../REBUILD.md](../../REBUILD.md), described end to end on one
platform.

This is a walkthrough, not a project to clone. There is no `wrangler` config and no Worker
source here, because the shape of the thing matters more than one vendor's syntax, and a
config file you copy without reading is how somebody else's naming ends up in your account.
Commands and snippets below are illustrative: read them, then write your own.

## What Cloudflare covers, and what it does not

| Piece | Product |
|---|---|
| Media lake | R2 |
| Report site | Pages |
| Campaign scheduling | Workers Cron Triggers |
| Work fan-out | Queues |
| Run state and leases | KV |
| Report index | D1, optional |
| **Capture** | **nothing; see [../bring-your-own/](../bring-your-own/)** |
| **Model inference** | **nothing; see [../bring-your-own/](../bring-your-own/)** |

Capture is a long-running transcode and Workers are request-scoped. Inference is GPU batch over
custom weights, and Workers AI serves a catalogue that does not include them. The Worker you
build here **schedules and tracks** that work. It does not do it.

---

## 1. Name everything from one prefix

Pick a prefix and derive every resource name from it. Do not let any script carry a real
account name as a default: that is how one deployment's identifiers reach another's estate.

```
<prefix>-lake             R2, the media lake
<prefix>-site-assets      R2, only what a publish gate has cleared
<prefix>-inference-work   Queue
<prefix>-inference-dlq    Queue, dead letters
<prefix>-run-state        KV
<prefix>-report-index     D1, optional
```

Create them with `wrangler r2 bucket create`, `wrangler queues create`,
`wrangler kv namespace create` and `wrangler d1 create`. Create the dead letter queue **before**
the queue that references it.

Keep the lake and the site assets separate. The lake holds source recordings under upstream
licence terms; site assets hold only material a rights gate has already cleared. One bucket for
both means one mistake away from publishing something you had no right to publish.

## 2. Protect the raw zone

`raw/` is the only copy of something that cannot be re-recorded.

```
wrangler r2 bucket lock add <prefix>-lake \
  --name raw-retention --prefix raw/ --retention-days 365
```

Then set an [object lifecycle](https://developers.cloudflare.com/r2/buckets/object-lifecycles/)
moving older objects to Infrequent Access. Mind the trade: Infrequent Access is cheaper per
GB-month but adds a retrieval charge and a 30-day minimum duration, so it suits the archive and
not the working set.

There is no deep-archive tier, so the cost curve differs from the Azure reference deployment.
Model it before you commit. Continuous audio across several feeds accumulates faster than people
expect, and a delete rule is not the answer when the archive is the system of record.

## 3. Credentials

Create a **scoped** R2 API token, not an account-wide one. Capture gets write on `raw/` and
nothing else, and specifically not delete.

Set anything secret with `wrangler secret put`. Never in a config file, and never as an argument
to a long-running process, where it sits readable on the process table for that process's whole
life.

## 4. The orchestration Worker

One Worker, with two Cron Triggers and a queue consumer. Cron expressions are UTC, and changes
take up to fifteen minutes to propagate.

**Bindings it needs:** the lake bucket, the work queue as a producer and a consumer, and the KV
namespace. Wrangler resolves R2 buckets and queues by name but **KV namespaces and D1 databases
by id**, so paste those ids in after creating them.

**Two schedules, because they answer different questions:**

```
0 9 * * *      daily sweep, lagging the capture day
*/30 * * * *   lease reaper
```

A `scheduled` handler receives which cron fired, so one Worker serves both. Dispatch on it
explicitly and log an unrecognised value rather than falling through: a silent default is how a
schedule quietly stops doing anything.

### The daily sweep

For each active feed and each model that runs against it:

1. Build the run key from `(model, feed, camera, day)`. **If it already exists in KV, skip.**
   That is your idempotency, and it is what makes a re-run free.
2. List the lake under the day's contract prefix, limit 1.
3. **If nothing is there, record `no_source_data` and move on.** No data is not a failure. It is
   a coverage gap, and it has to be recorded as one, because a day with no recording and a day
   with no detections look identical on a count.
4. Otherwise send a message to the work queue and record the run as queued.

**Lag the sweep behind the capture day.** Ask for the day that just ended and you read a partial
upload, then record a coverage gap that never existed. Two days back is a reasonable default.

**Select feeds on `active`**, which means "producing usable signal", not "its process is
running". Those are different questions and the difference has cost real data.

### The lease reaper

This runs on **its own schedule, not as a step inside the campaign.** That is the whole point.

For each lease in KV past its expiry: check whether the compute is genuinely busy, and if it is
not, release it and delete the lease.

Three rules that matter more than the code:

- **The lease is the contract.** Past expiry, an idle machine is reclaimed whether or not any
  reconciliation exists. Before expiry it is never touched.
- **If liveness cannot be read, hold and alert.** Never treat "do not know" as "not busy":
  that reclaims a machine mid-run.
- **If the platform is unreachable, raise.** An empty list means "nothing to reclaim" and looks
  exactly like success.

> In the reference deployment teardown lived inside the campaign runner and consulted that
> campaign's reconciliation, so the only code that released a machine was code that does not run
> when a campaign fails. One incident cost $27, the next $133, when a finished sweep left two
> machines running 86 hours past expiry.

### The queue consumer

Each message is one unit of inference work, handed to whatever compute you brought.

Keep batches small: a message is minutes of GPU work, so batching buys nothing and a large batch
loses more on a retry. Configure a **dead letter queue**; without one a poison message retries
until it ages out and the failure is invisible.

On failure, retry rather than acknowledge. An acknowledged failure is recorded as a processed
day, which is worse than a visible error.

---

## 5. The report site on Pages

The site is plain files: no build step, no framework, no runtime, no environment variables.

```
wrangler pages project create <your-project> --production-branch main
wrangler pages deploy <path-to-site-repo> --project-name <your-project>
```

Or connect the site repository in the dashboard. **Set the build command to empty and the output
directory to the repository root.** There is nothing to build, and a framework preset guessing
otherwise is the most likely way to break this.

### Headers

Content-addressed assets are immutable and can be cached hard. The index and roll-up change on
every publish.

```
/reports/*/assets/*
  Cache-Control: public, max-age=31536000, immutable

/index.html
  Cache-Control: public, max-age=300

/site-data.json
  Cache-Control: public, max-age=300
```

### Where the media lives

**In the repository** is usually right. Assets are bundled into the report directory at publish
time and committed, so the site is self-contained, a clone is a full backup, and there is no
second system to keep in step. The reference deployment does this at 99 MB across 14 reports.

**In R2, referenced by URL** is worth it past a few gigabytes. The cost is that a report is no
longer self-contained: an asset can be deleted from under a published page and nothing in the
publish gate will notice. If you do this, point the bundle verification at R2, or you lose the
guarantee that every reference in a published page resolves.

Do not mix the two. A site where some reports are self-contained and others are not is one where
nobody can say what a backup contains.

### What must not go here

No model code, no configuration, no credentials, no infrastructure detail. Keeping code out is
also what keeps copyleft and responsible-use licence terms from attaching to the published
pages. See [../../reference/PUBLISHING.md](../../reference/PUBLISHING.md).

### Verdict capture

The reference deployment keeps this browser-local: verdicts in `localStorage`, an export button,
nothing transmitted. That is what lets the site say it runs no server, accepts no input, stores
no accounts and sets no cookies.

D1 plus a Function would let readers submit verdicts directly. That is a genuinely useful upgrade
and also a different privacy posture, a moderation problem, and a new place for personal data to
accumulate. Make it a deliberate choice with its own notice, not a side effect of having a
database available.

---

## Cost note

The dominant cost is not storage. It is an idle inference machine nobody tore down: roughly $560
a month for one in the reference deployment.

Cloudflare does not charge egress, which changes one design decision: pulling data back out for
reprocessing is free, so there is less pressure to keep compute in the same cloud as the lake.
