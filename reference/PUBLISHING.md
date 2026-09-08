# Publishing

Reference for Stage 8 of [../REBUILD.md](../REBUILD.md).

```
bundle  ->  rights gate  ->  redaction gate  ->  site repository
```

Both gates run over the **finished bundle in a temporary directory**. A refused publish leaves
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

## Two things are computed, not stated

**The licence.** Most restrictive of any contributing feed, read from the registry. Two different
share-alike licences are refused rather than ranked, because that combination cannot be satisfied
at all.

**The coverage.** Read from run artifacts. Every source path goes through the path contract's
parser, so an off-contract path is counted and reported rather than silently averaged in.

Both are promises the methodology makes, so both are derived rather than asserted.

## What gets written

```
reports/<report-id>/index.html     the page, every asset reference rewritten
reports/<report-id>/report.json    the provenance record
reports/<report-id>/assets/...     content-addressed media
```

Plus a regenerated notice file, index and sitemap at the site root.

## Portability

Resolve every relative reference, copy media into the bundle, rewrite the page.
Content-address the assets, so an image referenced from forty cards is copied once.

Then **verify every local reference resolves inside the bundle**, and refuse if any does not.
That check exists because a page linking `../fused/annotated/...` produced 3,605 broken images
the moment it was copied away from a run directory that no longer existed.

What does not fit the byte budget is counted and reported on the page, never dropped silently.

## Rules for the site repository

- **Say inside it that it is generated**, or somebody will send a pull request that the next
  publish silently overwrites.
- **Reserve the names your generator uses for its own hub pages** and refuse to publish a report
  under one. Staging a report removes its destination directory first, so a collision destroys.
- **`report_id` is permanent.** It becomes a public URL path; changing it breaks every link
  already sent.
- **Keep a restyle step that reaches every page**, including pages whose builder no longer
  exists. See [../LIMITATIONS.md](../LIMITATIONS.md).
- **Publish, index, restyle, in that order.** Restyle is not optional and must be idempotent.
- **Publishing stages a change and stops.** A person pushes. Publishing is outward facing and
  cannot be undone by deleting the file afterwards.

## Review and verdicts

A reviewable page needs a stable identifier on every card. Refuse to make a page reviewable if
its cards carry none, rather than injecting a review layer that silently captures nothing.

**Keep verdict capture browser-local unless you decide otherwise deliberately.** Storing verdicts
in the reader's browser with an export button means the site runs no server, accepts no input,
stores no accounts and sets no cookies, which is a claim worth being able to make. A server-side
store is a reasonable upgrade and a different privacy posture, plus a moderation problem and a
new place for personal data. Make it an explicit choice with its own notice, not a side effect of
having a database available.
