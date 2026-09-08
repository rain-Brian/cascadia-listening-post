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

## Three defects worth designing against

All three were found in one published report in the reference deployment, all passed every gate
that existed at the time, and all are now fixed there and caught by the gate. Build the checks
in from the start and you will not meet them.

- **A report published without run directories carried no coverage.** The page builder supplied
  a window count, which satisfied the "has a coverage denominator" check, so nothing noticed that
  the period and the hours were null. For a duration-bearing source the hours are exactly
  derivable, so require them. **Do not** require them for stills or video: those units have no
  fixed duration, and multiplying 10,140 one-minute snapshots by a 30-second audio constant
  yields 84.5 "usable hours", which means nothing and would be a headline figure.
- **Model scores were recorded as prose.** `"Ecotype 1.00 Southern Resident, OrcaHello 0.97."`
  cannot be compared, sorted or thresholded, and the numbers it describes are then machine-readable
  nowhere. Validate that a confidence is a number in 0..1. Note that the sentence held *two*
  model scores and the field holds one, so a repair has to preserve the sentence somewhere or it
  loses a published figure.
- **The report declared one site and covered three**, naming the other two throughout the page.
  This is an attribution failure, and since `sites` is what the rights gate is fed, a feed with
  different terms would have produced the wrong licence. Check declared sites against per-camera
  counts, which is a second reason to derive coverage from the run.

**Do not check declared sites against the page prose.** That was tried and was wrong four times
in five: these pages carry a "quietly missing" section naming nodes that were offline, which is
the coverage honesty the methodology asks for, and flagging those pushes an operator to credit a
feed that contributed nothing.

One defect in that report remains open, and it is the interesting one: its published detection
count matches no definition reproducible from the run, at any site or in total. That is exactly
why a manifest should carry a `positive_definition` field saying what was counted. Two obvious
senses, "window with a positive prediction" and "window with at least one positive segment",
differ by 40% at one station in this data.

## Absence of detections is not absence of animals

Not a rebuild limitation, but the thing most often misreported, so it belongs here too.

A day with no detections and a day with no recording look identical on a count. Every report must
state how much usable signal it covers, and "usable" is stricter than "recording". A bridge can
hold a file handle open and write silence for five days while every liveness check reports
healthy. That happened, and it cost real data.
