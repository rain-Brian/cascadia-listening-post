# Upstream media rights

Reference for Stage 0 of [../REBUILD.md](../REBUILD.md).

**Rights live in the registry, not in prose.** The `rights` block on each feed is what the
publish gate reads. If this file and a registry ever disagree, the registry is correct. A fact
restated in prose drifts from the fact enforced in code.

## Procedure for adding a feed

1. Find the actual licence notice. Read its scope: notices often name data, methods and models,
   not just media, which may reach your spectrograms and derived detections.
2. Record the terms in the `rights` block, in **every** repository holding a copy of the
   registry. Check the copies match.
3. Record in `verified_by` what the position rests on. Say plainly when it rests on a published
   page rather than a written grant.
4. Set `commercial_use` to what the **holder permits**, not what you intend.
5. Set `derivatives_license` to what your derived work must carry. This is the field that
   decides a report's effective licence.

A feed defaults to `redistribute: unknown` and is unpublishable until this is done.

## The four positions

| Position | Example | You may publish derived media |
|---|---|---|
| Public domain | US Government work, 17 U.S.C. 105 | yes |
| Non-commercial share-alike | CC BY-NC-SA 4.0 | yes, with three obligations below |
| All rights reserved | standard video-platform licence | only with a grant, or a recorded authorisation |
| Unknown | unchecked feed | no |

### Public domain

Two caveats. Agencies host partner-owned content on the same sites and put the burden on you to
confirm which is which, so a position resting on a published page is "verified as far as the
published pages go". And **trademarks are protected separately from copyright**: a public-domain
photograph does not license the agency's emblem, and the emblem must never appear on your pages.

Attribution is often requested rather than required. Give it anyway.

### Non-commercial share-alike

Three obligations, all enforced rather than remembered:

1. **Attribution** in the exact form the operator asks for, including link text if specified.
2. **ShareAlike**: a report built from that material must carry the same licence. **This is why
   report licences are computed per report** rather than declared once for the site.
3. **NonCommercial**: clear commercial use with the holder first.

Record your non-commercial position deliberately rather than assuming it. The reference
deployment's is written down: the site is free, carries no advertising, sells nothing, and states
that it is a personal research project. The line to watch is not the site, it is reuse.

### All rights reserved

Public and reusable are different properties, and this is the case that proves it.

If you publish anyway on an institutional authorisation rather than a grant, say so in
`verified_by` in terms, so nobody later mistakes the two. And be precise about scale: a report
embedding several hundred annotated frames is redistribution of somebody's footage, not
commentary illustrated by it.

**If a holder objects: unpublish first, discuss after.** Set `redistribute` back to `no`, delete
the report directory, regenerate the index. Do not wait for agreement on whether the objection is
well founded.

## The rule that makes this tractable

> **None of this is commercial use. If something becomes commercial, it goes in a new
> repository.**

Two consequences, because the risk is drift rather than any deliberate decision:

- Nothing moves into paid work by being copied. Not a figure, not a table, not a detection count.
  The move is to a new repository, with rights cleared *before* the work starts.
- Clearing rights is per feed and per use. Permission to publish is not permission to sell.

## Model licences

Separate question, binding different things.

| Licence type | Binds | Effect |
|---|---|---|
| GPL-3.0 | the code | copyleft reaches what you link and distribute |
| RAIL | the **use** | restrictions can follow the model's outputs |
| MIT / BSD | the code | attribution, little else |
| Unrecorded | nothing safely | treat outputs as unclearable |

The RAIL family is the one people get wrong. It is not permissive-with-paperwork; it restricts
categories of use. Read it before deployment.

## Location precision

Publish coordinates at the precision the operator publishes, never finer. Prefer past windows to
live positions. Where you have used a nearby landmark because the operator publishes none, say so
in the `source` field rather than presenting it as the node's position.

This matters more than it looks for animals people would travel to see.
