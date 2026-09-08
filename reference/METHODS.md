# Methods

The rules that keep a published page honest. Reference for Stages 7 and 8 of
[../REBUILD.md](../REBUILD.md).

This is the part most worth copying. The infrastructure is replaceable; these rules are what
make the results mean anything.

## What a detection is

A model output. Nothing is a confirmed identification unless it says a person reviewed it, and
reviewed items must be visually distinct from model output.

Be precise about what each model answers. A call-presence detector answers whether a call is in
the window. It does not identify population, individual, or call type. If you want population,
that is a second model with its own error rate, and the first model's confidence does not
license it.

## False-positive floors

**Show a detection only if its confidence clears the floor measured for that label at that site.**

Measure floors, do not assume them: run windows where the label should not appear, and the rate
at which the model fires anyway is the floor.

Two rules, both learned by getting them wrong:

- **No measured floor, no card**, however confident the model was. The reference deployment once
  displayed a humpback label at 0.97 confidence when humpback had no measured floor at all.
- **Floors are per site, never pooled.** Pooling lets a busy site clear a threshold on its own
  volume and license claims at a quiet site that never earned one.

A worked example of the floors working: an 827-label backfill produced 5.90% at one hydrophone
against a 7.5% floor, and 1.74% at another. Both below floor, both correctly unpublished. The
temptation is to lower the threshold. A floor that moves when it is inconvenient is not a floor.

## Review queues

Some pages are not results. They are queues: model output published before anyone judged it, so
the queue can be checked and pipeline changes are visible from outside.

Mark a queue plainly, at the top. Nothing on one is an identification, and floors do not license
it, because a queue exists precisely where no floor has been measured.

Where a floor exists, a detection clears it or is not shown. Where none has been measured, the
honest choices are to publish nothing or to publish plainly labelled as unreviewed. Publishing it
is what lets a reader disagree with a specific card, and those disagreements are the material a
floor is eventually built from.

## Coverage

**Every report states how much usable signal it covers**, and "usable" is stricter than
"recording".

A day with no detections and a day with no recording look identical on a count. Coverage is the
only thing that separates them.

Read it from run artifacts, never type it. A hand-entered figure is a claim about provenance
rather than provenance. Where a domain is naturally counted in something other than hours (video
segments, frames analysed), record that count and name the unit rather than converting to hours
you did not measure.

## Negative controls

Test what the model does when the answer should be no. This is what separates a detection system
from a demonstration.

Record rejections as well as adoptions. The reference deployment evaluated a general whale
classifier and **rejected** it at 77.5% against the incumbent's 79.3%. Recording that stops the
next person re-evaluating it from scratch.

## Why the numbers are checkable

Three properties, all verifiable by a reader:

- **Site-level numbers are built from manifests, never scraped from pages.** A claim that exists
  only in prose cannot become a site-level figure.
- **The rights and redaction gates are code, not judgement.** No override flag.
- **The pipeline carries regression guards** for failures that have already happened once.

None of that makes the prose correct. It means figures are checkable against each report's
provenance record, and where prose and manifest disagree, the manifest is what the run produced.

## Disclose the AI agents

If pipeline code and page prose are written with AI coding agents, say so on the site.

Not ceremony: it changes what a reader should check. A language model can write a fluent sentence
about a number it did not compute, and the failure mode is a page that reads as authoritative
while describing something the run never produced.

## Corrections

Keep the record of what a model said on a given day as it was, including where it was wrong.
Record corrections alongside the original rather than replacing it.

A page that quietly edits its past errors cannot be used to judge the pipeline, and judging the
pipeline is the point.

## State these limits on the page itself

- A detection is a model output, not a sighting.
- Absence of detections is not absence of animals.
- Confidence is not probability of correctness.
- A floor measured at one site does not transfer to another.
- A queue is not a result.
