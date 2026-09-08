# Upstream media rights

Every feed this kind of system captures belongs to somebody else. This document is the
human-readable half of the rights position. The enforced half is the `rights` block on each
feed in the registry, which the publish gate reads.

**Rights live in the registry, not here.** This file explains how positions are reached. If the
two ever disagree, the registry is correct and this file is stale. That ordering is deliberate:
a fact restated in prose drifts from the fact enforced in code.

## The rule that makes this tractable

> **None of this is commercial use. If something becomes commercial, it goes in a new
> repository.**

That is a hard boundary in the reference deployment, and it is what makes non-commercial
licence terms safe to operate under rather than a thing to keep worrying about. Two
consequences, because the risk here is drift rather than any decision anyone would make
deliberately:

- **Nothing moves into paid work by being copied.** Not a figure, not a table, not a detection
  count, not a method write-up. The move is to a new repository, and the rights are cleared
  *before* the work starts, not after somebody notices.
- **Clearing rights is per feed and per use.** A licence cleared for one feed says nothing
  about another, and permission to publish says nothing about permission to sell.

If your organisation cannot make an equivalent commitment, resolve the commercial question
with every rights holder before you capture anything.

## The four positions you will meet

### Public domain (for example, US Government works)

The easiest case. Material created by a US federal agency is generally public domain under
17 U.S.C. 105 unless otherwise indicated.

Two caveats that are easy to miss. Agencies often host partner-owned or third-party content on
the same site and put the burden on you to confirm which is which, so a position resting on a
published page is "verified as far as the published pages go" rather than a written grant.
Record that distinction in `verified_by`. And agency **trademarks** are protected separately
from copyright: a public-domain photograph does not license the agency's emblem, and an emblem
must never appear on a derived page.

Attribution is often requested rather than required. Give it anyway.

### Non-commercial share-alike (for example, CC BY-NC-SA 4.0)

The most common licence on community science feeds, and the one with real consequences.

Three obligations follow, and all three should be enforced rather than remembered:

1. **Attribution** in the exact form the operator asks for. If they specify a hyperlink with
   particular link text, the registry carries the exact string and the renderer uses it.
2. **ShareAlike** means a report built from that material must itself carry the same licence.
   It cannot be relicensed more permissively. **This is why a report's licence is computed per
   report rather than declared once for the site**: a site-wide licence statement will be wrong
   for every report that touched share-alike material.
3. **NonCommercial**, which usually means commercial use must be cleared with the holder first.

Note that such notices frequently name not just audio or images but data, analytic methods and
models, and data products. Read the scope: it may reach your spectrograms, your extracted
clips, and arguably your derived detection data.

**A position on NonCommercial should be recorded deliberately rather than assumed.** In the
reference deployment the reasoning is written down: the published site is free, carries no
advertising, sells nothing, and states plainly that it is a personal research project
unaffiliated with any employer. That is non-commercial on any ordinary reading, so no
permission was sought. The line to watch is not the site, it is reuse.

### All rights reserved (for example, a standard video-platform licence)

A live stream on a video platform carries that platform's standard licence by default, which
reserves all rights to the channel owner. Public and reusable are different properties, and
this is the case that proves it.

If you publish from such a feed, be honest in the registry about what the position actually
rests on. In the reference deployment one feed is published on **operator authorisation** based
on an existing institutional partnership, and `verified_by` says in terms that this is not a
written grant, so nobody reading it later mistakes the two.

Be precise about what is being published. A report embedding several hundred annotated frames
is redistribution of somebody's footage, not commentary illustrated by it. The fair-use footing
for two or three frames supporting a specific claim is strong; for a browsable archive of four
hundred it is weak.

**If a holder objects: unpublish first, discuss after.** Set `redistribute` back to `no`, delete
the report directory, and regenerate the index. Do not wait for agreement on whether the
objection is well founded.

### Unknown

The default for a feed nobody has checked, and it is unpublishable. That is the correct
default: publishing material you had no right to publish is not a mistake that deleting it
afterwards undoes.

## Model licences bind different things

Media rights and model licences are separate questions and they constrain different things.

| Licence type | What it binds | Practical effect |
|---|---|---|
| GPL-3.0 | The code | Copyleft reaches what you link it into and distribute |
| RAIL | The **use** | Restrictions can follow the model's outputs, not just the model |
| MIT / BSD | The code, permissively | Attribution, little else |
| Unrecorded | Nothing safely | Treat outputs as unclearable until settled |

The RAIL family is the one that surprises people. It is not permissive-with-paperwork; it
restricts categories of use, and those restrictions can follow derived outputs. Read it before
deployment.

A model with no recorded licence and no retrieval URL is an open gap on two fronts at once: it
cannot be re-fetched from a clean clone, and its licence position is unknown. See
[LIMITATIONS.md](LIMITATIONS.md).

**Keeping model code out of the public artifact is what keeps these questions from gating a
share.** That is the whole reason for the capture/inference/site split described in
[ARCHITECTURE.md](ARCHITECTURE.md).

## Adding a feed

A new feed defaults to `redistribute: unknown` and is therefore unpublishable. To change that:

1. Find the terms. Read the actual notice, not a summary of it.
2. Record them in the `rights` block in the registry, in **every** repository that carries a
   copy, and check the copies match.
3. Note in `verified_by` what evidence the position rests on, and say plainly when it rests on
   published pages rather than a written grant.
4. Set `commercial_use` to what the **holder permits**, not to what you happen to be doing. It
   stays `permission_required` or `unknown` even while every use is non-commercial, because it
   describes their position and not yours.

Do not set `redistribute: yes` because a feed is publicly viewable.

## Location precision

Publish coordinates at the same approximate precision the feed operator publishes, never finer,
and prefer reporting past windows over live positions. Where an operator publishes no
coordinates and you have used a nearby public landmark, say so in the `source` field rather
than presenting it as the node's position.

This matters more than it looks for animals people would travel to see.
