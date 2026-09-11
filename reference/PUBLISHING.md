# Publishing

Reference for Stage 8 of [../REBUILD.md](../REBUILD.md).

```
build  ->  rights gate  ->  redaction gate  ->  quality gate  ->  index  ->  restyle  ->  verify site
```

The gates run over the **finished bundle in a temporary directory**. A refused publish leaves
nothing behind, which matters because a half-written bundle in the site repository gets committed
by the next `git add -A` and never looked at again.

## Gate 1: rights

Refuses any feed whose `redistribute` is not `yes`. **No override flag.** A gate that can be
waived under deadline is not a gate.

Contributing feeds are declared explicitly by the caller, never inferred from the page. A gate
that works out its own inputs is checking its own homework.

## Gate 2: redaction

A content scan for hostnames, deployment paths, secret stores, storage accounts, service unit
names, signed URL parameters, account keys, connection strings, GUIDs, operator home directories,
private and public addresses, secret-shaped environment assignments, and bearer tokens.

A **content scan over the finished artifact**, not a rule about how pages are written, because
the leak that matters is the one nobody meant to write: a run directory path in an error string,
a hostname in a debug comment, a signed URL pasted into a caption.

Text files only. Media is skipped: an image cannot leak a hostname in a form these patterns
catch, and scanning base64 for GUID-shaped runs produces only false positives.

Overrides take a **specific literal string, never a rule**, and every use is recorded in the
published provenance record rather than living in somebody's shell history.

Implementation and rule reasoning: [../tools/redact.md](../tools/redact.md).

## Gate 3: science and coverage

The first two gates decide whether a page may be published. This one decides whether its numbers
can be checked. It reads the finished artifact, not the process that built it, so it reaches every
page whatever produced it.

When `review_status` asserts detections, refuse unless:

- **The positive count is in the manifest.** A number that exists only on the page cannot be
  compared with anything.
- **The manifest says what it counted** in `positive_definition`. One run's summaries carried two
  senses of "positive" that differed by 40% at one station, and a page conflated them.
- **The page shows evidence**, or `evidence_waiver` says why not. Thousands of detections with none
  shown leaves a reader nothing to check.
- **Every known contaminant at the declared sites is addressed** in `contaminant_screening`, by
  name. The gate wants disclosure, not a particular choice: "not screened, counts include it"
  passes. Silence does not.

Always refuse:

- A missing or unrecognised `review_status`. An absent status must not take the free pass that
  `source quality gap`, the one deliberate exemption, gets.
- An audio report that analysed windows and records no hours or no dates.
- Hours on stills.
- A confidence that is not a number in 0..1.
- A camera in the per-camera counts that `sites` does not declare.

**Warn, never refuse, on a null window when runs are listed.** Detections are not held back over a
provenance field; the site marks that report's dates as inferred.

Keep known contaminants in a registry per site, each with the measurement that identified it and
when. Apply the screen as a required build step, not an option.

## Three things are computed, not stated

**The licence.** Most restrictive of any contributing feed, read from the registry. Two different
share-alike licences are refused rather than ranked, because that combination cannot be satisfied
at all.

**The coverage.** Read from run artifacts. Every source path goes through the path contract's
parser, so an off-contract path is counted and reported rather than silently averaged in.

**The model identity.** Names resolve through one registry, with aliases for earlier spellings, and
licence, lineage and caveat come from it. One detector reached the reference deployment's manifests
under two names and four version strings, and the public index then said it had no recorded caveat.

All three are promises the methodology makes, so all three are derived rather than asserted.

## What gets written

```
reports/<report-id>/index.html     the page, every asset reference rewritten
reports/<report-id>/report.json    the provenance record
reports/<report-id>/assets/...     content-addressed media
```

Plus, at the site root, a regenerated notice file, index, sitemap, `site-data.json` roll-up, and
the shared stylesheet under `assets/`. **Stage all of them**, from one named list. A list naming
only reports and the index would ship pages linking a stylesheet the site does not carry, beside a
roll-up describing the previous publish.

## Portability

Resolve every relative reference, copy media into the bundle, rewrite the page.
Content-address the assets, so an image referenced from forty cards is copied once.

Then **verify every local reference resolves inside the bundle**, and refuse if any does not.
That check exists because a page linking `../fused/annotated/...` produced 3,605 broken images
the moment it was copied away from a run directory that no longer existed.

One reference is exempt: the site's shared stylesheet. It cannot exist inside a bundle, restyle
owns the link, and the site verifier checks that it resolves in the real site. Exempt exactly that
path, so a report's own media and look-alike file names are still checked.

Copy media beside the page rather than adding run directories as search roots: two cameras can
produce same-named files on the same day, and a search would resolve one to the other.

What does not fit the byte budget is counted and reported on the page, never dropped silently.

## Rules for the site repository

- **Say inside it that it is generated**, or somebody will send a pull request that the next
  publish silently overwrites.
- **Reserve the names your generator uses for its own hub pages** and refuse to publish a report
  under one. Staging a report removes its destination directory first, so a collision destroys.
- **`report_id` is permanent.** It becomes a public URL path; changing it breaks every link
  already sent.
- **Keep a restyle step that reaches every page**, including pages whose builder no longer
  exists. See [../LIMITATIONS.md](../LIMITATIONS.md). It must be able to take things back off a
  page as well as add them.
- **Publish, index, restyle, verify, in that order.** Restyle is not optional and must be
  idempotent. A failing verify stops the change.
- **Publishing stages a change and stops.** A person pushes. Publishing is outward facing and
  cannot be undone by deleting the file afterwards.

## Correcting a public report

Keep what a page said. Correct it in the open.

- **Retire, do not edit.** When a report's title and contents disagree, or a newer report strictly
  supersedes it, replace the page with a stub naming its successor, with a `canonical` link and
  `noindex`, and remove its `report.json`. The URL still resolves, and the report drops out of
  every index and total with no special case.
- **Repair a manifest from the run that produced it**, through a tool, never by hand in the
  generated site. Refuse when the run disagrees with the report, and never write a zero over a
  null: a zero is a claim, a null is an absence.
- **Where the run is gone, backfill with provenance**: `verified_from_run`, `verified_from_page`,
  `inferred_from_key`, or `not_recoverable`. The last one gains no numbers.
- **When a repair moves a value out of a field, keep the original sentence.** A prose confidence
  can hold two model scores; the numeric field holds one.

## Review and verdicts

A reviewable page needs a stable identifier on every card. Refuse to make a page reviewable if
its cards carry none, rather than injecting a review layer that silently captures nothing.

**Keep verdict capture browser-local unless you decide otherwise deliberately.** Storing verdicts
in the reader's browser with an export button means the site runs no server, accepts no input,
stores no accounts and sets no cookies, which is a claim worth being able to make. A server-side
store is a reasonable upgrade and a different privacy posture, plus a moderation problem and a
new place for personal data. Make it an explicit choice with its own notice, not a side effect of
having a database available.
