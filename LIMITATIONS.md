# Limitations

What a rebuild cannot reproduce, and what will cost you more than it looks like.

Read this before [REBUILD.md](REBUILD.md). Every item here was discovered the expensive way.

## One model cannot be obtained

The ecotype classifier used for marine audio (`birdnet07`) has **no recorded licence and no
retrieval URL**. It cannot be re-fetched from a clean clone of anything. It exists as a file
on one machine.

This is not a gap you can work around by looking harder. Until its provenance is settled,
anything it produced should be treated as unclearable, and a rebuild should assume ecotype
classification is unavailable.

**What you lose.** Call-presence detection still works: you can answer "was a killer whale
call present in this window". You cannot answer "which population is this call more
consistent with". Reports that distinguish Southern Resident from Bigg's are out of reach.

**What to do instead.** Treat ecotype as a separate, later problem with its own model
selection, its own measured false-positive floors, and its own licence review. Do not
substitute another classifier and keep the same report language.

## Model licences bind different things

| Model | Licence | What it binds |
|---|---|---|
| YOLO-Fish | GPL-3.0 | The code. Copyleft reaches anything you link it into and distribute |
| OrcaHello | RAIL, conservation-oriented | **Use**, with restrictions that can follow derived outputs |
| MegaDetector | MIT | Permissive |
| Ecotype classifier | Unknown | Unresolved. See above |

The RAIL licence is the one people get wrong. It is not a permissive open-source licence with
extra paperwork. It restricts categories of use, and those restrictions can follow the outputs
of the model, not just the model. **Read it before deployment, not after.**

If you intend to distribute anything you build, get the GPL-3.0 and RAIL positions written
down first. That review gates handover, it does not follow it.

## Two feed types are not freely reusable

**Non-commercial share-alike feeds.** Hydrophone audio in the reference deployment is
CC BY-NC-SA 4.0. Three obligations follow and none of them are optional: attribution in a
specified form, share-alike carrying into your derived work (so a report built from that audio
must itself be share-alike), and non-commercial use only. If your organisation would use the
outputs commercially, you need permission from the rights holder before you start, not after.

**Feeds published on operator authorisation rather than a grant.** The aquarium video feed in
the reference deployment carries a YouTube Standard Licence, which reserves all rights to the
channel owner. **No grant of any kind was obtained.** It is published on the operator's own
authorisation, resting on an existing partnership.

That authorisation is not transferable and does not extend to you. If you point a rebuild at a
similar feed, you are starting from "all rights reserved" and you need your own written
permission. The registry records this honestly: `verified_by` says in terms that it is not a
written grant, so nobody reading it later mistakes the two.

Be precise about what redistribution means here. A report embedding several hundred annotated
frames is redistribution of the operator's footage, not commentary illustrated by it. The
fair-use footing for two or three frames supporting a specific claim is strong. For a
browsable archive of four hundred it is weak.

## Cloudflare cannot host two of the tiers

This matters if you read [deploy/cloudflare/](deploy/cloudflare/) as a complete answer. It is
not one.

**Capture** is long-running `ffmpeg` processes holding a connection open for hours or days,
supervised by an init system that restarts them. Workers are request-scoped. There is no
shape of Workers, Durable Objects or Cron Triggers that runs a continuous transcode.

**Model inference** is GPU batch work over hours of audio and video. Workers AI serves a
catalogue of hosted models, and the models here are not in it: they are custom weights with
custom pre- and post-processing. You cannot run OrcaHello or YOLO-Fish on Workers AI by
choosing a different model name.

Both tiers need somewhere else. See [deploy/bring-your-own/](deploy/bring-your-own/). What
Cloudflare does cover, and covers well, is the object store, the static site, the scheduler and
the queue.

## Two paths in the reference deployment were built and never ran

Do not copy these. They are documented so you recognise them if you meet them.

**The event-driven consumer.** An Event Hubs and Event Grid path exists, provisioned, with a
managed identity. It has never processed a message. The identity was never granted a role, and
the consumer as written is a `tee`: it tails from the live edge so a restart skips the backlog,
it calls a checkpoint API with no checkpoint store configured, it filters nothing (so writebacks
re-trigger it), and it launches no job.

**The scheduled runbooks.** Three runbooks exist, published, with schedules attached to a
registered worker. All schedules are disabled and the job history is empty. The blocking
dependency was the same role assignment.

The scheduler that actually runs is a timer on the maintainer's laptop. A rebuild should
implement the intended orchestration properly rather than copy either the dead path or the
laptop.

**The lesson worth carrying over**, because it recurred three times: the fix existed and was
not in the path that executes. Merged but not deployed. Scheduled but disabled. Built and
tested but left unmerged. Building it is not shipping it.

## Some published reports cannot be regenerated

In the reference deployment, three published reports have no builder left in the repository and
their run directories are gone. They exist only as rendered HTML.

This is why the site carries a restyle step that rewrites already-published pages: it is the
only mechanism that reaches every page regardless of what produced it. If you build a
publishing pipeline, either keep every builder or accept that you will need such a step. Do not
assume you can re-render your archive from manifests.

## Reproducibility is not free

The reference deployment does not pin dependencies with `==` or carry a lockfile, pins one
model revision to a moving branch, sets no seeds, and spans three separate virtual
environments for a single finalize step. Two VMs provisioned a week apart resolve different
tensor library versions for the same sweep.

If you are rebuilding, fix this at the start rather than inheriting it. It is Layer 6 in
[ARCHITECTURE.md](ARCHITECTURE.md) and it is much cheaper before you have results to reconcile.

## Absence of detections is not absence of animals

Not a rebuild limitation, but the one that most often gets misreported, so it belongs here too.

A day with no detections and a day with no recording look identical on a count. Every report
must state how many hours of usable signal it covers, and "usable" is a stricter test than
"recording". A bridge can hold a file handle open and write silence for five days while every
liveness check reports healthy. That happened in the reference deployment and cost real data.

See [METHODS.md](METHODS.md) for how coverage is computed and why it is read from run
artifacts rather than typed.
