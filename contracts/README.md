# Contracts

The data shapes the system agrees on. Schemas only, no implementation.

Build these first. In the reference deployment they came last, and the cost was measurable:
the blast radius of a single schema change was roughly fourteen edit sites across two
repositories and three languages, with no test that would have caught a missed one. Three
independent implementations of the partition builder disagreed with each other, and the
production uploader implemented none of them.

| File | Shape |
|---|---|
| [`lake-path.md`](lake-path.md) | Where artifacts live in the object store |
| [`feeds.schema.json`](feeds.schema.json) | The feed registry: what exists, and what may be published |
| [`feeds.example.json`](feeds.example.json) | A worked registry, with infrastructure fields removed |
| [`detection-record.schema.json`](detection-record.schema.json) | One detection, from any model |
| [`ingestion-event.schema.json`](ingestion-event.schema.json) | One capture or transfer event |
| [`run-manifest.schema.json`](run-manifest.schema.json) | What a single inference run did |
| [`report.schema.json`](report.schema.json) | The provenance record beside every published page |
| [`site-data.schema.json`](site-data.schema.json) | The roll-up that drives the landing page |

## Three rules that make these worth having

**Validate on write, in every producer.** A schema nothing enforces is documentation, and
documentation drifts. The point of the contract is that an off-contract write fails at the
producer rather than surfacing as a wrong number in a report six weeks later.

**Refuse rather than guess.** Every parser here should reject an off-contract input instead of
coercing it. The reference implementation's predecessor extracted a date from a path with a
shell prefix-strip, and when the path did not contain the expected marker the expansion
returned the whole string, so results were written to a partition named after the zone. No
validation, no error, no way to notice.

**Version every record.** `schema_version` on every row, from the first row. Adding it later
means a migration over data you cannot re-derive.

## Field conventions

`feed` and `camera` are the two-part identity of a source, and together they key everything
else. `feed` is the operator or family (`orcasound`, `nps`), `camera` is the specific node.
Neither ever contains a slash.

Timestamps are UTC, ISO 8601, with an explicit offset or trailing `Z`. Dates without times are
`YYYY-MM-DD`.

`run_id` identifies one execution of one model over one range. It appears on every record that
execution produced, which is what makes a bad run retractable.

Nulls are meaningful and are not the same as absent. `spdx: null` on a public-domain feed says
"no SPDX identifier applies", which is a verified position. A missing `spdx` key says nobody
looked.
