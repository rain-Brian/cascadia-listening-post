# Publishing

How a finished run becomes a page at a public URL.

```
bundle  ->  rights gate  ->  redaction gate  ->  site repository
```

Both gates run over the **finished bundle in a temporary directory**. A refused publish leaves
nothing behind. That matters more than it sounds: a half-written bundle in the site repository
gets committed by the next `git add -A` and then never looked at again.

## Publishing stages, it does not push

The publish step should stage a change and stop. Publishing is outward facing and cannot be
undone by deleting the file afterwards, so it stays a decision a person makes explicitly.

The report identifier becomes a public URL path and is **permanent**. Changing it breaks every
link already sent.

## Gate 1: rights

Refuses any feed whose `redistribute` is not `yes` in the registry. **There is no override
flag.** A gate that can be waived under deadline is not a gate.

The contributing feeds are declared explicitly by the caller and never inferred from the page.
A gate that works out its own inputs is checking its own homework.

See [RIGHTS.md](RIGHTS.md).

## Gate 2: redaction

Refuses hostnames, deployment paths, key vaults, storage accounts, service unit names, signed
URL parameters, account keys, connection strings, GUIDs, operator home directories, private
network addresses, environment assignments and bearer tokens.

This is a **content scan over the finished bundle**, not a rule about how pages are written,
because the leak that matters is the one nobody meant to write: a run directory path in an
error string, a hostname in a debug comment, a signed URL pasted into a caption. None of those
are things a renderer sets out to emit.

It scans text files only. Media is skipped: an image cannot leak a hostname in a form this
catches, and scanning megabytes of base64 for GUID-shaped runs produces only false positives.

An override takes a **specific literal string, never a rule**, and every use is recorded in the
published provenance record, so an override is visible in the artifact rather than only in
somebody's shell history.

A reference implementation of the rule set is in [tools/redact.md](tools/redact.md).

## What gets written

```
reports/<report-id>/index.html     the page, with every asset reference rewritten
reports/<report-id>/report.json    the provenance record
reports/<report-id>/assets/...     content-addressed media
```

Plus a regenerated notice file, index and sitemap at the site root.

## Two things are computed, not stated

**The licence.** A report takes the most restrictive terms any contributing feed imposes, read
from the registry. Reports built from share-alike material carry that licence whatever the site
default says. Two different share-alike licences are refused rather than ranked, because that
combination cannot be satisfied at all.

**The coverage.** Hours of usable signal are read from the run's own artifacts, never typed.
Every source path goes through the path contract's parser, so an off-contract path is counted
and reported rather than silently averaged in.

Both are promises the methodology makes, so both have to be derived rather than asserted.

## Portability

Resolve every relative reference, copy the media into the bundle, and rewrite the page.
Content-address the assets, so an image referenced from forty cards is copied once.

Then **verify that every local reference resolves inside the bundle**, and refuse if any does
not. That check exists because a page linking `../fused/annotated/...` produced 3,605 broken
images the moment it was copied away from a run directory that no longer existed.

What does not fit the byte budget is counted and reported on the page, never dropped silently.

## The site repository is generated

Say so in the site repository itself, because otherwise somebody will send a pull request
against it and a merge will be overwritten without warning by the next publish.

Reserve the names your generator uses for its own hub pages, and refuse to publish a report
under one. Staging a report removes its destination directory first, so a collision is
destructive.

Keep a restyle step that can reach every published page, including pages whose builder no
longer exists. See [LIMITATIONS.md](LIMITATIONS.md).

## Order matters

Publish, then regenerate the index, then restyle. The restyle step is not optional: it applies
the shared stylesheet and rewrites already-published HTML deliberately. Run it every time, and
keep it idempotent.

## Review and verdicts

A reviewable page needs a stable identifier on every card. Refuse to make a page reviewable if
its cards carry none, rather than injecting a review layer that silently captures nothing.

In the reference deployment this is where the queue backlog is stuck: only one of several page
builders emits card identifiers, so pages from the others cannot be published as reviewed even
though the review layer, the verdict parser and the export path all exist. Emit the identifier
from every builder, from the start.

**Keep verdict capture browser-local unless you have decided otherwise deliberately.** Storing
verdicts in the reader's browser and offering an export means the site runs no server, accepts
no input, stores no accounts and sets no cookies, which is a claim worth being able to make. A
server-side verdict store is a reasonable upgrade and a different privacy posture; make it an
explicit choice with its own notice, not a side effect of choosing a hosting product.
