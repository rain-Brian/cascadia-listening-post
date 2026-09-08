# Limitations

Read this before [REBUILD.md](REBUILD.md). Every item was discovered the expensive way.

## One model cannot be obtained

The ecotype classifier (`birdnet07`) has **no recorded licence and no retrieval URL**. It cannot
be re-fetched from a clean clone of anything.

**Effect:** call-presence detection works, so you can answer "was a killer whale call present in
this window". You cannot answer "which population is this call more consistent with". Reports
distinguishing Southern Resident from Bigg's are out of reach.

**Do not** substitute another classifier and keep the same report language. Treat ecotype as a
separate problem with its own model selection, its own measured floors, and its own licence
review.

## Model licences bind different things

| Model | Licence | Binds |
|---|---|---|
| YOLO-Fish | GPL-3.0 | the code; copyleft reaches what you distribute |
| OrcaHello | RAIL, conservation-oriented | the **use**; restrictions can follow outputs |
| MegaDetector | MIT | the code, permissively |
| Ecotype classifier | unknown | nothing safely |

The RAIL licence is the one people get wrong. It is not permissive-with-paperwork. Read it before
deployment, not after.

If you intend to distribute what you build, settle the GPL-3.0 and RAIL positions first. That
review gates handover; it does not follow it.

## Two feed types are not freely reusable

**Non-commercial share-alike** (the hydrophone audio): attribution in a specified form,
share-alike carrying into your derived work, and non-commercial use only. If your organisation
would use the outputs commercially, get permission before you start.

**Published on operator authorisation rather than a grant** (the aquarium video): the feed carries
a standard video-platform licence reserving all rights to the channel owner. **No grant was
obtained.** It is published on the operator's own authorisation, resting on an existing
partnership.

That authorisation is not transferable and does not extend to you. Point a rebuild at a similar
feed and you start from "all rights reserved", needing your own written permission.

## Cloudflare cannot host two of the tiers

**Capture** is long-running `ffmpeg` holding a connection open for hours, supervised by an init
system. Workers are request-scoped. No arrangement of Workers, Durable Objects or Cron Triggers
runs a continuous transcode.

**Inference** is GPU batch over custom weights with custom pre- and post-processing. Workers AI
serves a catalogue of hosted models, and these are not in it.

Both need somewhere else: [deploy/bring-your-own/](deploy/bring-your-own/). What Cloudflare covers
well is the object store, the static site, the scheduler and the queue.

## Two paths were built and never ran

Do not copy these. They are here so you recognise them.

**The event-driven consumer.** Provisioned with a managed identity, has never processed a message.
The identity was never granted a role, and the consumer as written tails from the live edge (so a
restart skips the backlog), calls a checkpoint API with no checkpoint store configured, filters
nothing (so writebacks re-trigger it), and launches no job.

**The scheduled runbooks.** Three published, with schedules attached to a registered worker. All
schedules disabled, job history empty, blocked on the same role assignment.

What actually runs is a timer on the maintainer's laptop. Implement the intended orchestration
properly rather than copying either.

## Some published reports cannot be regenerated

Three published reports have no builder left in the repository and their run directories are gone.
They exist only as rendered HTML.

This is why the site carries a restyle step that rewrites already-published pages: it is the only
mechanism reaching every page regardless of what produced it. If you build a publishing pipeline,
either keep every builder or accept you will need such a step. **Do not assume you can re-render
your archive from manifests.**

## Reproducibility is not free

The reference deployment does not pin dependencies with `==` or carry a lockfile, pins one model
revision to a moving branch, sets no seeds, and spans three virtual environments for a single
finalize step. Two machines provisioned a week apart resolve different tensor library versions for
the same sweep.

Fix this at the start rather than inheriting it. It is much cheaper before you have results to
reconcile.

## Known defects in the reference deployment's own data

Two, both visible in published `report.json` files, both unfixed. Your schemas should be stricter
than these:

- **`window.usable_hours` is null in 11 of 14 reports.** Video reports count segments instead,
  which is legitimate, but the methodology promises coverage and the manifest does not always
  carry it.
- **`featured_findings[].confidence` sometimes holds prose** rather than a number, so it cannot be
  sorted or thresholded, and the number it describes is recorded nowhere machine-readable.

## Absence of detections is not absence of animals

Not a rebuild limitation, but the thing most often misreported, so it belongs here too.

A day with no detections and a day with no recording look identical on a count. Every report must
state how much usable signal it covers, and "usable" is stricter than "recording". A bridge can
hold a file handle open and write silence for five days while every liveness check reports
healthy. That happened, and it cost real data.
