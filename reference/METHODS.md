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

When a model in the chain did not run, say so on the page ("ecotype not assessed") and rank by
the model that did. Never describe the output of a classifier that did not see the input.

## Name each count for what it holds

A count and its definition travel together. Key names such as `model_candidates`,
`source_units_with_positive_segment` and `marine_review_candidates` tell a reader whether a
number counts boxes, windows or rows before anyone opens the definition.

Where one run supports two senses of "positive", record both and say which is which. In the
reference deployment "window with a positive model verdict" and "window with at least one positive
segment" differed by 40% at one station, and publishing the wrong one reversed a claim.

## False-positive floors

**Show a detection only if its confidence clears the floor measured for that label at that site.**

Measure floors, do not assume them: run windows where the label should not appear, and the rate
at which the model fires anyway is the floor.

Two rules, both learned by getting them wrong:

- **No measured floor, no card**, however confident the model was. The reference deployment once
  displayed a humpback label at 0.97 confidence when humpback had no measured floor at all.
- **Floors are per site, never pooled.** Pooling lets a busy site clear a threshold on its own
  volume and license claims at a quiet site that never earned one.

**Above the floor is not enough; it has to be separable from it.** Test the rate against the floor
and publish nothing for a label that cannot be told apart. At one hydrophone the reference
deployment found 10 of 108 (9.3%) against a 7.5% floor, p=0.29, so that site shows nothing for
that label and says why.

A worked example of the floors working: an 827-label backfill produced 5.90% at one hydrophone
against a 7.5% floor, and 1.74% at another. Both below floor, both correctly unpublished. The
temptation is to lower the threshold. A floor that moves when it is inconvenient is not a floor.

## Known contaminants

Some sites produce a sound or an object the model fires on. Identify each one once, record the
measurement and the date, and screen for it before counting. A report at that site states what
was done about it, even when the answer is nothing.

A screen that measures the real thing removes it where it was found and almost nothing elsewhere.
In the reference deployment a resonance at one hydrophone, screened blind over six days of new
audio, removed 1,002 detections there and exactly one at each of the other two.

Volume is not quality. The busiest station in that data had the lowest share of detections the
ecotype classifier recognised: 17.7%, against 48.5% at a quieter one.

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

A parameter measured per run, such as a night and day threshold derived from each run's own
frames, is reported per run. A single figure for a batch is a number no run found.

## Moments and statements

A card about a moment carries the instant it was seen: a bear at 19:02:59. A card about a dataset,
such as a rate over a month or a measurement at one node, carries the window it was drawn from.
Never stamp a statement with an instant it did not have.

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
- **The rights, redaction and quality gates are code, not judgement.** No override flag.
- **The pipeline carries regression guards** for failures that have already happened once.

None of that makes the prose correct. It means figures are checkable against each report's
provenance record, and where prose and manifest disagree, the manifest is what the run produced.

## Disclose the AI agents

If pipeline code and page prose are written with AI coding agents, say so on every page, not only
on a methods page. A shared link lands a reader on a report.

Not ceremony: it changes what a reader should check. A language model can write a fluent sentence
about a number it did not compute, and the failure mode is a page that reads as authoritative
while describing something the run never produced.

## Corrections

Keep the record of what a model said on a given day as it was, including where it was wrong.
Record corrections alongside the original rather than replacing it, and retire a report rather
than editing it: see [PUBLISHING.md](PUBLISHING.md#correcting-a-public-report).

A page that quietly edits its past errors cannot be used to judge the pipeline, and judging the
pipeline is the point.

## State these limits on the page itself

- A detection is a model output, not a sighting.
- Absence of detections is not absence of animals.
- Confidence is not probability of correctness.
- A floor measured at one site does not transfer to another.
- A queue is not a result.
