# Methods

What the outputs of this kind of pipeline can and cannot support, and the rules that keep a
published page honest.

This is the part most worth copying. The infrastructure is replaceable; the discipline below is
what makes the results mean anything.

## What a detection is

A model output. Nothing is a confirmed identification unless it says a person reviewed it, and
reviewed items should be marked and kept visually distinct from model output.

Be precise about what each model answers. A call-presence detector answers whether a call of a
given kind is in the window. It does not identify population, individual, or call type, and no
page should be read as saying it does. If you want population, that is a second model with its
own error rate, and it is not licensed by the first one's confidence.

## False-positive floors

**A detection is shown only if its confidence clears the false-positive floor measured for that
specific label at that specific site.**

Floors are measured, not assumed. Take windows where the label should not appear, run them
through the model, and the rate at which it fires anyway is the floor.

Two rules follow, and both were learned by getting them wrong.

**A label with no measured floor gets no card, however confident the model was.** The reference
deployment once displayed a humpback label at 0.97 confidence when humpback had no measured
floor whatsoever. High confidence from a model you have not characterised at that site is not
evidence, it is a number.

**Floors are per site, never pooled.** Pooling lets a site with heavy traffic clear a threshold
on its own volume and then license claims at a quiet site that never earned one. That happened
and was corrected.

A worked example of the floors doing their job: an 827-label backfill produced detections at
5.90% at one hydrophone against a 7.5% floor and 1.74% at another. Both below floor, both
unpublished, correctly. The temptation in that moment is to lower the threshold. Do not. A
floor that moves when it is inconvenient is not a floor.

## Review queues

Some pages are not results. They are **queues**: model output published before anyone has
judged it, so the queue itself can be checked and so changes to the pipeline can be seen from
outside.

Mark a queue page plainly, at the top. Nothing on one is an identification. The floors above do
not license it and cannot, because a queue typically exists precisely where no floor has been
measured.

Where a floor exists, a detection clears it or is not shown. Where none has been measured, the
honest choices are to publish nothing or to publish the output plainly labelled as unreviewed.
Publishing it is what lets a reader disagree with a specific card, and those disagreements are
the material a floor is eventually built from.

## Coverage

**Every report states how many hours of usable signal it covers**, and "usable" is a stricter
test than "recording".

This is the number that stops a reader treating a quiet day as an unrecorded one. A day with no
detections and a day with no recording look identical on a count, and they are not the same
thing.

Read coverage from run artifacts, never type it. A hand-entered hours figure is a claim about
provenance rather than provenance. Where a domain is naturally counted in something other than
hours (video segments, frames analysed), record that count and say which unit it is, rather
than converting to hours you did not measure.

## Negative controls

Test what the model does when the answer should be no. This is the discipline that separates a
detection system from a demonstration.

A worked example from the reference deployment: a general whale classifier was evaluated as a
possible addition and **rejected**, at 77.5% against the incumbent's 79.3%. Recording the
rejection matters as much as recording the adoption, because otherwise the next person
re-evaluates it from scratch.

## Where the numbers come from

Three properties make a site's figures checkable, and a reader can verify all three:

**Site-level numbers are built from manifests, never from pages.** The index and roll-up are
generated from each report's provenance record. Nothing scrapes a rendered page for a fact, so
a claim that exists only in prose cannot become a site-level figure.

**The rights and redaction gates are code, not judgement.** A feed whose terms do not permit
redistribution is refused at publish time, with no override flag.

**The pipeline carries a test suite**, including regression guards for failures that have
already happened once.

None of that makes the prose correct. It means the figures are checkable against each report's
provenance record, and where prose and manifest disagree, the manifest is what the run actually
produced.

## Disclose the AI agents

If the pipeline code and page prose are written with AI coding agents, say so on the site.

This is not ceremony. It changes what a reader should check. A language model can write a
fluent sentence about a number it did not compute, and the failure mode is a page that reads as
authoritative while describing something the run never produced. The three properties above are
what limit that, and naming the risk is what tells a reader to use them.

## Corrections

Keep the record of what a model said on a given day as it was, including where it was wrong.
Record corrections alongside the original rather than replacing it.

A page that quietly edits its past errors cannot be used to judge the pipeline, and judging the
pipeline is the point.

## Limits worth stating on the page itself

- A detection is a model output, not a sighting.
- Absence of detections is not absence of animals.
- Confidence is not probability of correctness.
- A floor measured at one site does not transfer to another.
- A queue is not a result.
