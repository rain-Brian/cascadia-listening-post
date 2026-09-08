# Wildlife Stack

How to rebuild a continuous wildlife detection pipeline on your own resources.

This repository is documentation and deployment configuration. It carries no model code and
no credentials. It exists so that an organisation can stand up the system that produces
[Cascadia Listening Post](https://rain-Brian.github.io/wildlife-detections/) without needing
access to the private repositories that run it.

## What the system does

Public media feeds are captured continuously, archived to an object store, run through
detection and classification models, and turned into review reports that a person reads and
judges. Capture and inference are separate processes: nothing that detects runs inside the
process that records, so a model change cannot cost recording time.

| Workstream | Feeds | Models |
|---|---|---|
| Marine audio | Hydrophones | Call-presence detection, ecotype classification |
| Underwater video | Aquarium camera | YOLO-Fish with a YOLO-World second pass |
| Terrestrial video | Fixed webcams | MegaDetector |
| Operations | The capture and transfer tier itself | Deterministic rules, with an advisory LLM tier |

## Start here

| Question | Document |
|---|---|
| What are the pieces and how do they fit | [ARCHITECTURE.md](ARCHITECTURE.md) |
| How do I actually build it | [REBUILD.md](REBUILD.md) |
| What can I not rebuild, and why | [LIMITATIONS.md](LIMITATIONS.md) |
| What are the data shapes | [contracts/](contracts/) |
| How does a run become a public page | [PUBLISHING.md](PUBLISHING.md) |
| Who owns the media and what may I publish | [RIGHTS.md](RIGHTS.md) |
| What do the numbers on a report mean | [METHODS.md](METHODS.md) |
| Where do LLM agents fit | [AGENTS.md](AGENTS.md) |
| How do I keep infrastructure detail out of a public artifact | [tools/redact.md](tools/redact.md) |

**Read [LIMITATIONS.md](LIMITATIONS.md) before you start.** Parts of this system cannot be
reproduced from a clean start, and one of the models cannot be obtained at all. Knowing that
first will save you a week.

## Checking this repository

```sh
python3 tools/check_redaction.py .          # nothing here names real infrastructure
python3 tools/test_redaction.py             # the rules still catch real leaks
PUBLISHED_SITE=<a-site-repo> bash tools/verify.sh   # everything, including schemas
```

The schemas in `contracts/` are validated against data from a running deployment, not written
from memory: `report.schema.json` and `site-data.schema.json` are checked against published
pages. Point `PUBLISHED_SITE` at a site repository to repeat that.

## What this repository is not

It is not a distribution of the pipeline. There is no `pip install`, no container image, and
no model weights here. You write the implementation, or you obtain it from its upstream
sources under their own licences.

That boundary is deliberate. The inference tier combines GPL-3.0 model code with a
RAIL-licensed model whose terms carry use restrictions into derived work. Keeping code out of
this repository keeps those obligations from attaching to the documentation, and keeps the
licence question where it belongs, which is with whoever assembles a running system.

## The four-repository shape

The reference implementation is split four ways, and the split is worth copying:

| Repository | Holds |
|---|---|
| hub | Architecture, decisions, rights positions. Runs nothing |
| capture | Capture, forward, archive. No model code, ever |
| inference | Models, decision layer, report generation, orchestration |
| site | Rendered reports only. Public. No code, no configuration |

Two boundaries hold it apart and both earn their keep. **Capture never runs a model**, which
is what lets the inference tier carry restrictive model licences without those reaching the
capture tier. **The public site carries no code**, which is what keeps those same licences
from gating a share of the results.

## Licence

Prose in this repository is CC BY 4.0. Configuration, schemas and scripts are MIT. See
[LICENSE](LICENSE).

Neither licence grants you any right in the upstream media feeds, the models, or the
published reports. See [RIGHTS.md](RIGHTS.md).

## Affiliation

A personal research project by Brian Rain. Not a Microsoft product, and not affiliated with
or endorsed by the Microsoft AI for Good Lab, Orcasound, the National Park Service, or any
other feed operator.
