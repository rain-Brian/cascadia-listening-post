# Lake path contract

Where an artifact lives in the object store. One implementation builds these and one parses
them. Not two, and not four across three languages, which is what the reference deployment had
before it was consolidated.

## The layout

```
{zone}/{feed}/{camera}/yyyy=YYYY/mm=MM/dd=DD/{filename}
manifests/ingestion/yyyy=YYYY/mm=MM/dd=DD/events.jsonl
logs/{service}/{filename}
inference/{model}/{feed}/{camera}/yyyy=YYYY/mm=MM/dd=DD/{filename}
inference/{model}/runs/{run_id}/{filename}
```

`CONTRACT_VERSION` is `1`.

## Zones

| Zone | Holds | Partitioned |
|---|---|---|
| `raw` | What the capture process recorded, unmodified | yes |
| `sent` | What was forwarded to a downstream consumer | yes |
| `prepared` | Derived artifacts built for a specific consumer | yes |
| `manifests` | Operational events, one owner per subtree | yes |
| `logs` | Service logs | **no, by design** |
| `inference` | Model output | yes |

**`logs` is flat on purpose.** Its files are append-mode logs held open for the lifetime of a
service, so there is no per-file capture date to partition on. Partitioning them would mean
choosing between the date a log was opened and the date a line was written, and neither is a
property of the file.

## The date is the capture date

The partition comes from the **artifact filename**, which every capture process writes as
`<something>_YYYYMMDDTHHMMSS[Z].<ext>`.

**There is no modification-time fallback, deliberately.** An artifact belongs to the day it was
captured. A modification time is the day it was last touched, which for a file that has been
copied, synced or re-uploaded is a different day. A file that cannot be dated from its name is
one the caller should refuse, not misfile.

Date validation is strict: a real calendar date, year between 2000 and 2999, month 1 to 12, day
within that month's actual length. A malformed date fails loudly rather than resolving to a
partition nobody meant to write to.

## Parse refuses, it does not guess

```
raw/orcasound/bush_point/yyyy=2026/mm=08/dd=06/bush_point_20260806T182000Z.wav   valid
raw/orcasound/bush_point/audio/bush_point_20260806T182000Z.wav                  refused
raw/orcasound/bush_point/yyyy=2026/mm=8/dd=6/...                                refused
raw/orcasound/bush_point/yyyy=2026/mm=02/dd=30/...                              refused
```

The second case is the one that matters. It is what a plain recursive sync produces if the
local tree has an extra directory level, and it is off-contract even though it looks
reasonable. A parser that tolerates it is a parser that will eventually write a result
somewhere nobody looks.

## Decide the partition question once

Either your uploader partitions by date, or your contract is a flat sync. Pick one, before you
have data.

In the reference deployment these disagreed for months without anyone noticing. The production
uploader did a flat recursive sync with no date partitions at all, while two out-of-band
uploaders synthesised them, so two incompatible layouts accumulated in the same container. A
downstream job extracted the date by stripping everything up to `yyyy=`; against flat paths
there was no such marker, so the expansion returned the entire string and every result was
written to `yyyy=raw/mm=raw/dd=raw/`. Silently.

Migrating afterwards is possible (the reference deployment moved 269,674 blobs onto the
contract) but it is a job you can avoid entirely by choosing on day one.

## Testing

Keep a golden fixture file of path-to-components pairs, and test **both** the builder and the
parser against it, in every language that touches a path. Round-trip property tests
(construct, parse, construct again) catch the asymmetric bugs that unit tests miss.

If a second language needs to build paths, it gets the same fixture file and asserts the same
results. That is what stops the two halves drifting.
