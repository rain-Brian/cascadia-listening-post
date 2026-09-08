# Bring your own: capture and inference

The two tiers no serverless platform hosts for you. Stated as requirements rather than a
prescription, because the right answer depends on what you already run.

## Capture

**Shape of the workload.** One long-running process per feed, holding a network connection open
for hours or days, writing segmented output. Modest CPU, negligible GPU, steady disk write.
Restarted by an init system when it dies, which it will.

**What it needs**

- A host that stays up and runs an init system with restart policies and failure hooks.
- Local disk sized for the buffer between capture and transfer, plus headroom. Alert on
  **projected time to full**, not percent used.
- Write credentials to the raw zone of the object store, and no more than that. Capture should
  not be able to delete.
- Outbound network to the feeds. Nothing inbound.

**A single machine is enough** for a handful of feeds. The reference deployment runs eight
bridges on one general-purpose VM. This is not the expensive part.

**Four things to get right at the start**, because retrofitting them is unpleasant:

1. **A start-up grace period before any watchdog may act.** Some sources publish a growing
   playlist that a decoder treats as on-demand, so it starts from the beginning and needs
   minutes to reach the live edge. A watchdog restarting on stale output at two minutes makes
   such a feed unrecoverable by construction: it never reaches live, and the restart is the
   reason. This cost twenty hours of one feed in the reference deployment, and it took a live
   reproduction to see it.
2. **Separate the supervision budget from the remediation budget.** If the init system allows N
   restarts per interval and the watchdog also restarts, they exhaust the same budget together,
   the unit ends up failed permanently, and nothing re-arms it.
3. **Guard the restart call.** Under `set -e`, a restart of an already-failed unit exits
   non-zero and aborts the whole watchdog sweep, so every service later in the list goes
   unchecked that cycle.
4. **Never let a fetch failure produce a plausible artifact.** A camera bridge that reuses its
   last good frame when a fetch fails keeps the archive perfectly fresh while the camera is
   dead. If you cannot fetch, write nothing and report it.

**One feed may not run where the others do.** Sources needing browser cookies or interactive
authentication cannot run headless on a shared host. Keep that in the registry as a property of
the feed rather than a special case in code.

## Inference

**Shape of the workload.** Batch. Read a day of artifacts, run a model, write detections, exit.
GPU for video models; audio models often run acceptably on CPU. Bursty: idle most of the day,
saturated for an hour.

**What it needs**

- Compute you can create and destroy on demand. Reserved capacity is the wrong shape for this.
- Read access to the raw zone, write access to the inference zone.
- A pinned environment: a lockfile and a container image per model.
- A place to write run status that survives the machine, so an interrupted run is resumable.

**Options, roughly in order of how much you already have**

| Option | Fits when |
|---|---|
| Kubernetes Jobs | You already run a cluster |
| Managed container jobs (Cloud Run Jobs, Container Apps Jobs, Batch) | You want no cluster |
| Cloud VMs created per campaign | Simplest to reason about; needs disciplined teardown |
| Your own hardware | Steady volume, and you own a GPU |

**Cloudflare Containers** can run a container on demand, and is worth evaluating for the
CPU-bound audio path. It is not a fit for the GPU video path today. Check current GPU
availability before designing around it.

## The teardown rule

Whatever provisions compute owns destroying it, with a hard time-to-live as a backstop, and
**teardown must not be a step inside the success path**.

This is the single most expensive lesson in the reference deployment, and it recurred. Teardown
ran inside the campaign runner and consulted that campaign's reconciliation, so the only code
that released a machine was code that does not execute when a campaign fails. One incident cost
$27, the next $133, when a finished sweep left two machines running 86 hours past an expired
lease while the fix sat in an unmerged branch.

Make the lease the contract:

- Past `lease-expires`, an idle machine in a known group is reclaimed whether or not any
  reconciliation exists.
- Before expiry it is never touched.
- Require live evidence of work before holding a machine past expiry. A "busy" check that reads
  a field carrying no CPU information is inert, and inert guards are worse than absent ones
  because they are trusted.
- If liveness cannot be read, **hold** rather than reclaim, and alert.
- If the cloud is unreachable, raise rather than return an empty list. An empty list means
  "nothing to reclaim" and looks like success.

Run it on its own schedule, independent of any campaign. See `reapExpiredLeases` in
[../cloudflare/src/index.js](../cloudflare/src/index.js).

## Credentials

Never on the command line. A long-running process with a key in its argument vector exposes it
to any local user for the life of that process, continuously. This applies to stream keys,
storage account keys, signed URLs and bearer tokens alike.

Pass secrets through the environment where the tool reads them directly, through a
configuration file with restrictive permissions, or through standard input. Set a restrictive
umask **before** writing any rendered configuration rather than tightening permissions
afterwards, and write to a temporary file with an atomic rename so a failure mid-render cannot
truncate a working config.

Grant the capture user only the specific service-control verbs it needs. Blanket passwordless
privilege escalation collapses the file-permission boundary the restrictive modes rely on.
