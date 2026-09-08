# Contributing

Corrections and additions are welcome, especially from anyone who has tried to follow
[REBUILD.md](REBUILD.md) and found it wrong.

## Most useful

**A step that does not work.** If you followed the rebuild path and hit something that is
incomplete, out of date, or simply false, that is the most valuable report. Say which document,
which step, and what actually happened.

**A platform mapping.** The capability table in [ARCHITECTURE.md](reference/ARCHITECTURE.md) covers
Cloudflare and Azure. A worked example for another platform is welcome, in the same shape as
[deploy/cloudflare/](deploy/cloudflare/): parameters with no defaults, and honest about what the
platform cannot do.

**A rights position.** If you have cleared terms with a feed operator, the reasoning is worth
recording. See [RIGHTS.md](reference/RIGHTS.md).

## Please do not send

**Model code, weights, or anything that would make this repository a distribution of the
pipeline.** The absence of code is what keeps copyleft and responsible-use licence terms from
attaching to this documentation, and that boundary is not negotiable. See
[LIMITATIONS.md](LIMITATIONS.md).

**Infrastructure identifiers from any real deployment.** Hostnames, storage accounts, key
vaults, subscription identifiers, service unit names, operator paths. Every example here is a
parameter or a placeholder and must stay that way.

**Marketing.** This documents a small research pipeline honestly, including where it is broken.
Claims it cannot support do not belong here.

## Style

Say what went wrong, not only what to do. Nearly every rule in these documents exists because
something failed, and the failure is usually more convincing than the rule. Where a document
states a cost or a duration, it is a real one from a real incident; keep it that way rather than
rounding it into an illustration.
