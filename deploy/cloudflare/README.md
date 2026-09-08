# Cloudflare: worked example

Stages 2, 9 and 10 of [../../REBUILD.md](../../REBUILD.md).

A complete path for the parts of the system Cloudflare hosts well, and an honest account of the
two parts it does not host at all.

## What this covers

| Piece | Product |
|---|---|
| Media lake | R2 |
| Report site | Pages |
| Campaign scheduling | Workers Cron Triggers |
| Work fan-out | Queues |
| Report index | D1, optional |
| Run state and config | KV |

## What this does not cover

**Capture** and **model inference**. Neither fits Workers, and no configuration in this
directory pretends otherwise.

Capture is a long-running transcode holding a connection open for hours. Workers are
request-scoped, and there is no arrangement of Workers, Durable Objects or Cron Triggers that
changes that. Inference is GPU batch work with custom model weights and custom pre- and
post-processing; Workers AI serves a catalogue of hosted models and these are not in it.

See [../bring-your-own/](../bring-your-own/). The Worker here schedules and tracks that work.
It does not do it.

## Files

| File | What it is |
|---|---|
| `setup.sh` | Provisions the account resources. Every name is a required parameter |
| `wrangler.jsonc` | The orchestration Worker |
| `src/index.js` | The scheduled handler, as a working skeleton |
| `pages.md` | Publishing the report site |

## Order

Set `CF_PREFIX` in your environment to the prefix every resource is named from, then:

```sh
./setup.sh            # R2 buckets, queues, KV, D1
npx wrangler deploy   # the orchestration Worker
```

`setup.sh` requires `CF_PREFIX` and has no default for it, so a missing value stops the run
rather than provisioning into a name somebody else chose.

Then follow `pages.md` for the site.

## Storage classes and retention

R2 has two storage classes, Standard and Infrequent Access. Infrequent Access is cheaper per
GB-month but adds a data retrieval charge and a 30-day minimum duration, so it suits the
archive and not the working set. Set transitions with
[object lifecycles](https://developers.cloudflare.com/r2/buckets/object-lifecycles/).

There is no equivalent of a deep archive tier, so the cost profile differs from the Azure
reference deployment. Model it before you commit: continuous audio capture across several
feeds accumulates faster than people expect, and the archive is the system of record, so a
delete rule is not the answer.

**Consider a bucket lock on the raw zone.** Retention policies protect the archive from
accidental or malicious deletion, which matters because the raw zone is the only copy of
something that cannot be re-recorded:

```sh
npx wrangler r2 bucket lock add "$CF_PREFIX-lake" \
  --name raw-retention --prefix raw/ --retention-days 365
```

Cloudflare does not charge egress, which changes one design decision from the reference
deployment: pulling data back out for reprocessing is free, so there is less pressure to keep
compute in the same cloud as the lake.

## Cost note

The reference deployment's dominant cost was not storage, it was an idle GPU batch machine
nobody tore down: roughly $560 a month for one, and $133 lost in a single incident where a
finished sweep left two running 86 hours past an expired lease.

Whatever you use for inference, make the lease the contract and make teardown independent of
whether the campaign succeeded. See Layer 5 in [../../ARCHITECTURE.md](../../reference/ARCHITECTURE.md).
