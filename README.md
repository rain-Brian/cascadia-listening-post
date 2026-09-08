# Cascadia Listening Post: build instructions

How to build a continuous wildlife detection pipeline over public media feeds, on your own
resources.

Public hydrophones and cameras are recorded around the clock, run through detection models, and
turned into reports that show what was found and how far it can be trusted. This is the
instruction set for building that. The reference deployment publishes at
[rain-Brian.github.io/wildlife-detections](https://rain-Brian.github.io/wildlife-detections/).

**Start with [LIMITATIONS.md](LIMITATIONS.md), then work through [REBUILD.md](REBUILD.md).**

## Before you start

Read [LIMITATIONS.md](LIMITATIONS.md) first. One model cannot be obtained at all, two feed types
are not freely reusable, and two of the tiers do not run on serverless platforms. Fifteen
minutes there will save you a week.

You need:

- An object store, and somewhere to run two long-lived things (capture) and one bursty thing
  (inference). See [deploy/](deploy/).
- Feeds you have cleared the rights on. See [reference/RIGHTS.md](reference/RIGHTS.md).
- Each model, obtained from its own upstream source. **This repository contains no model code
  and no weights.**

## The stages

Each is a section of [REBUILD.md](REBUILD.md), with commands and a verification step.

| # | Stage | Skippable |
|---|---|---|
| 0 | Rights and licences | no |
| 1 | Contracts | no, and do it first |
| 2 | Object store | no |
| 3 | Capture | no |
| 4 | Signal health | no, and earlier than feels necessary |
| 5 | Transfer | if capture writes straight to the store |
| 6 | Inference | no |
| 7 | Measure false-positive floors | no, before publishing any detection |
| 8 | Reports and publishing | no |
| 9 | The site | no |
| 10 | Orchestration | yes, at first |
| 11 | Advisory agents | yes |

## Layout

| Path | What |
|---|---|
| [REBUILD.md](REBUILD.md) | The instruction set |
| [LIMITATIONS.md](LIMITATIONS.md) | What cannot be reproduced, and why |
| [contracts/](contracts/) | JSON Schemas for every artifact the system writes |
| [deploy/cloudflare/](deploy/cloudflare/) | Worked example in text: R2, Pages, Workers, Queues |
| [deploy/azure/](deploy/azure/) | The reference deployment, as a shape |
| [deploy/bring-your-own/](deploy/bring-your-own/) | Capture and GPU inference requirements |
| [tools/](tools/) | Redaction gate, schema validator, `verify.sh` |
| [reference/](reference/) | Why the instructions say what they say |

## Checking this repository

```sh
python3 tools/check_redaction.py .    # names no real infrastructure
python3 tools/test_redaction.py       # the rules still catch real leaks
bash tools/verify.sh                  # everything, including schemas
```

Set `PUBLISHED_SITE` to a site repository first, and `verify.sh` will also check the report
schemas against pages that actually shipped.

The schemas are validated against a running deployment rather than written from memory.

## What this repository is not

Not a distribution of the pipeline. No `pip install`, no container image, no weights.

That boundary is deliberate: the inference tier combines GPL-3.0 model code with a
RAIL-licensed model whose terms carry use restrictions into derived work. Keeping code out
keeps those obligations from attaching to the instructions, and leaves the licence question
with whoever assembles a running system.

## Licence

Prose is CC BY 4.0. Configuration, schemas and scripts are MIT. See [LICENSE](LICENSE).

Neither grants any right in the upstream feeds, the models, or any published report.

## Affiliation

A personal research project by Brian Rain. Not a Microsoft product, and not affiliated with or
endorsed by the Microsoft AI for Good Lab, Orcasound, the National Park Service, or any other
feed operator.
