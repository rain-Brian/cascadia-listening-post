# Rebuild

The ordered path from an empty account to a published report.

Read [LIMITATIONS.md](LIMITATIONS.md) first. Some of this cannot be reproduced, and knowing
which parts before you start will save you a week.

## Before anything technical

**Settle the rights.** Pick your feeds and record their terms in the registry before you
capture a byte. A feed defaults to `redistribute: unknown`, which is unpublishable, and that is
the correct default. See [RIGHTS.md](RIGHTS.md).

**Settle the model licences.** If you intend to distribute what you build, get the copyleft and
responsible-use positions written down now. This gates handover; it does not follow it.

**Decide the commercial question.** Non-commercial feed terms are safe to operate under only if
you can commit to non-commercial use. If you cannot, clear it with each holder first.

## Stage 0: the contracts

Do this before provisioning anything.

1. Copy [contracts/](contracts/) into your project.
2. Write **one** implementation of lake path construction and parsing, in one language. If a
   second language needs it, give it the same golden fixture file and assert the same results.
3. Decide the partition question once: partitioned by date, or a flat sync. Write it down.
4. Build your feed registry from [contracts/feeds.example.json](contracts/feeds.example.json),
   with your feeds and their real rights blocks.

You now have the thing that makes everything after this cheaper. Resist the urge to skip it:
the reference deployment deferred it and paid roughly fourteen edit sites across two
repositories and three languages for a single schema change.

## Stage 1: object store

Provision the media store and nothing else yet.

- One container or bucket, with the zone layout from
  [contracts/lake-path.md](contracts/lake-path.md).
- A lifecycle policy from day one: cool at 30 days, archive at 90, **no delete rule**. Storage
  is cheap and the archive is the system of record.
- Credentials that are not account keys, if your provider offers a workload identity. If it
  does not, or the grant is blocked, use keys but pass them through the environment rather than
  command-line arguments. See Layer 7 in [ARCHITECTURE.md](ARCHITECTURE.md).

Verify: write a file at a contract path, read it back, and confirm your parser round-trips it.

## Stage 2: capture

This is the tier Cloudflare cannot host. See
[deploy/bring-your-own/](deploy/bring-your-own/).

One long-running process per feed, under an init system, writing completed segments to the
`raw` zone.

Get these right at the start, because retrofitting them is unpleasant:

- **A start-up grace period** before any watchdog may act. Some sources take minutes to reach
  the live edge, and a watchdog that restarts at two minutes makes them unrecoverable by
  construction.
- **Separate supervision from remediation.** If the init system allows N restarts per interval
  and your watchdog also restarts, they exhaust the same budget together and the unit stays
  failed forever.
- **Write completed segments**, and have health checks read only completed ones.

Verify: kill a capture process and confirm it comes back, that the event is reported, and that
the watchdog still evaluates every other feed in the same sweep.

## Stage 3: signal health

**Do this before inference.** It is the highest value per unit of work in the system, and
without it you can record silence for weeks while every check reports green.

Emit crest factor, high-to-low frequency ratio and mains prominence per feed over completed
segments. Seed thresholds from a period you know was good.

Verify: replay an archived period that contains a known failure and assert the check alarms
**before** the date the failure was noticed. If you have no such period yet, keep the harness
and come back to it.

## Stage 4: transfer

If capture writes locally first, add a spool with explicit state, backoff, and a disk guard
that alerts on projected time to full rather than percent used.

Verify: fill a scratch volume and confirm the guard alerts before 100%. Kill an upload
mid-transfer and confirm it resumes without duplicating manifest rows. **Then test the prune
path specifically**: assert nothing is deleted when the sync reports a hard failure, that
nothing outside the retention window is deleted when it succeeds, and that an unrecognised
transfer message fails closed. Pruning is usually the only code in the system that destroys
data and it is usually the only code with no test.

## Stage 5: inference

Also not a Cloudflare tier. Lease compute, run, tear down.

- Obtain each model from its upstream source under its own licence. Nothing here distributes
  weights.
- Pin everything: dependencies with a lockfile, model revisions by digest rather than a branch.
- One container image per model. Not three virtual environments assembled by hand.
- Write detections through the contract, validated on write.

**Make the lease the contract.** Whatever provisions compute owns destroying it, with a hard
time-to-live as a backstop, and reclamation must not be a step inside the success path. In the
reference deployment teardown ran only where a campaign had reconciled, so a failed campaign
left machines running: 86 hours past expiry on one occasion.

Verify: run the same input twice with the same identity key and confirm no duplicate work.
Build from the lockfile on two clean hosts and confirm identical resolved dependencies and
identical output.

## Stage 6: measure your floors

Before you publish anything as a detection.

For each label at each site, run windows where the label should not appear and record the rate
at which the model fires anyway. That rate is the floor for that label at that site. Store the
floors with the date they were measured.

A label with no measured floor gets no card. If that leaves you with nothing publishable, you
publish a queue instead, plainly marked. See [METHODS.md](METHODS.md).

## Stage 7: reports and publishing

Build pages from run artifacts, then run the two gates. See [PUBLISHING.md](PUBLISHING.md).

- Emit a stable card identifier from **every** page builder, from the first one. Retrofitting
  it is what currently blocks the reference deployment's review backlog.
- Compute the licence and the coverage. Never type either.
- Keep the site repository generated, and say so inside it.

Verify: publish a report built from a feed marked `redistribute: no` and confirm it is refused.
Put a hostname in a page caption and confirm redaction refuses it. Both should fail closed.

## Stage 8: the site

The easy part. The site is plain files: no build step, no framework, no runtime.

Requirements are only that the host serves your JSON, audio and video with correct content
types and does not run a static-site generator over your raw HTML.

See [deploy/cloudflare/](deploy/cloudflare/) for a worked example.

## Stage 9: orchestration

Only now. A scheduled sweep over a date range is enough, and it is resumable, which an
event-driven path is not until you have built the checkpointing properly.

Add alerts as code, split per service so one stuck condition cannot mask its neighbours, plus a
rule that fires when any alert instance has been active beyond a threshold.

## Stage 10: agents

Advisory only. See [AGENTS.md](AGENTS.md). Enforce the boundary in the harness, by giving the
model no tools, rather than in the prompt.

## The failure mode to watch for throughout

Across three separate incidents in the reference deployment, the same thing happened: **the fix
existed and was not in the path that executes.** Merged to main but not deployed to the running
copy. Scheduled in the cloud but disabled. Built and tested but left in an unmerged branch.

Building it is not shipping it. Check what is actually running.
