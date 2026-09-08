#!/usr/bin/env bash
# Provision the Cloudflare account resources for a wildlife detection pipeline.
#
# Every resource name derives from CF_PREFIX, which is required. There are no
# defaults on purpose: a deploy script with a real account name baked in as a
# fallback is how one deployment's identifiers end up in another's estate.
#
# Idempotent. Re-running reports what already exists rather than failing.
set -Eeuo pipefail

: "${CF_PREFIX:?CF_PREFIX is required, e.g. export CF_PREFIX=cascadia}"

WRANGLER="${WRANGLER:-npx wrangler}"

LAKE="$CF_PREFIX-lake"
SITE_ASSETS="$CF_PREFIX-site-assets"
WORK_QUEUE="$CF_PREFIX-inference-work"
DEAD_QUEUE="$CF_PREFIX-inference-dlq"
STATE_KV="$CF_PREFIX-run-state"
INDEX_DB="$CF_PREFIX-report-index"

say() { printf '\n== %s\n' "$1"; }
tolerate_exists() { "$@" || printf '   (already exists, continuing)\n'; }

say "R2: media lake"
tolerate_exists $WRANGLER r2 bucket create "$LAKE"

say "R2: site assets"
# Separate from the lake. The lake holds source recordings under upstream
# licence terms; this holds only what a publish gate has already cleared.
tolerate_exists $WRANGLER r2 bucket create "$SITE_ASSETS"

say "Queues: inference work and dead letters"
tolerate_exists $WRANGLER queues create "$DEAD_QUEUE"
tolerate_exists $WRANGLER queues create "$WORK_QUEUE"

say "KV: run state"
# Holds campaign checkpoints and lease records. Small, hot, and must survive a
# Worker restart. Not the place for anything you cannot rebuild.
tolerate_exists $WRANGLER kv namespace create "$STATE_KV"

say "D1: report index (optional)"
# Only needed if you want to query reports. A generated JSON file is genuinely
# enough for a few hundred reports, and it is one less thing to keep in step.
tolerate_exists $WRANGLER d1 create "$INDEX_DB"

cat <<NEXT

== Provisioned, named from CF_PREFIX=$CF_PREFIX

  lake bucket    $LAKE
  site assets    $SITE_ASSETS
  work queue     $WORK_QUEUE
  dead letters   $DEAD_QUEUE
  state kv       $STATE_KV
  report index   $INDEX_DB

Next:

  1. Copy the KV namespace id and D1 database id printed above into
     wrangler.jsonc. Wrangler does not resolve these by name.

  2. Set a retention lock on the raw zone. It is the only copy of something
     that cannot be re-recorded:

       $WRANGLER r2 bucket lock add "$LAKE" \\
         --name raw-retention --prefix raw/ --retention-days 365

  3. Add a lifecycle rule moving the archive to Infrequent Access. Mind the
     30-day minimum duration and the retrieval charge; it suits the archive,
     not the working set.

  4. Set the credentials your capture and inference tiers use to reach R2.
     Create a scoped R2 API token rather than an account-wide one, and give
     capture write access to the raw zone only.

     Store it with 'wrangler secret put', never in this file and never in an
     argument to a long-running process, where it sits readable on the
     process table for the life of that process.

NEXT
