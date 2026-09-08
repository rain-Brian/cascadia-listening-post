/**
 * Orchestration Worker: decides what should run, records what did.
 *
 * Principle 0 applies here. This Worker is deterministic. It contains no model
 * and calls no language model. If you add an advisory agent, it reads what this
 * writes; it never writes what this reads. See ../../AGENTS.md.
 *
 * What this does NOT do, deliberately:
 *   - capture a feed (long-running transcode, not a Worker workload)
 *   - run a model (GPU batch with custom weights)
 *   - publish a report (a person runs the publish gates explicitly)
 */

const ZONE_RAW = "raw";

export default {
  async scheduled(controller, env, ctx) {
    switch (controller.cron) {
      case "0 9 * * *":
        return void ctx.waitUntil(planDailySweep(env));
      case "*/30 * * * *":
        return void ctx.waitUntil(reapExpiredLeases(env));
      default:
        // An unrecognised cron means wrangler.jsonc and this switch have
        // drifted. Say so; a silent default is how a schedule quietly stops
        // doing anything.
        console.error(`unhandled cron: ${controller.cron}`);
    }
  },

  /**
   * Queue consumer. Each message is one unit of inference work, handed to
   * whatever compute you brought. See ../bring-your-own/.
   */
  async queue(batch, env, ctx) {
    for (const msg of batch.messages) {
      try {
        await dispatchToCompute(msg.body, env);
        msg.ack();
      } catch (err) {
        // retry() rather than ack(), so a transient compute failure is not
        // recorded as a processed day. After max_retries this lands in the
        // dead letter queue, which is the point of having one.
        console.error(`dispatch failed for ${msg.body?.run_id}: ${err}`);
        msg.retry();
      }
    }
  },
};

/**
 * Find days that have capture data but no completed run, and enqueue them.
 *
 * The lag matters: asking for the day that just ended reads a partial upload
 * and records a coverage gap that never existed.
 */
async function planDailySweep(env) {
  const day = utcDayOffset(-2);
  const feeds = await loadActiveFeeds(env);

  for (const { feed, camera, models } of feeds) {
    for (const model of models) {
      const runKey = `run/${model}/${feed}/${camera}/${day}`;

      // Idempotency. The key is (model, feed, camera, day); a re-run of the
      // same sweep must produce no duplicate work.
      if (await env.RUN_STATE.get(runKey)) continue;

      const prefix = `${ZONE_RAW}/${feed}/${camera}/${dayPrefix(day)}`;
      const listed = await env.LAKE.list({ prefix, limit: 1 });
      if (listed.objects.length === 0) {
        // No data is not a failure. It is a coverage gap, and it has to be
        // recorded as one: a day with no recording and a day with no
        // detections look identical on a count and are not the same thing.
        await env.RUN_STATE.put(
          runKey,
          JSON.stringify({ status: "no_source_data", day, recorded_at: nowIso() })
        );
        continue;
      }

      await env.WORK.send({
        schema_version: 1,
        run_id: `${model}-${feed}-${camera}-${day}`,
        model_name: model,
        feed,
        camera,
        source_prefix: prefix,
        requested_at: nowIso(),
      });

      await env.RUN_STATE.put(
        runKey,
        JSON.stringify({ status: "queued", day, requested_at: nowIso() })
      );
    }
  }
}

/**
 * Reclaim compute whose lease has expired.
 *
 * This runs on its own schedule, NOT as a step inside the campaign. That is
 * the whole point. In the reference deployment teardown lived inside the
 * campaign runner and consulted that campaign's reconciliation, so the only
 * path that released a machine was the path that does not execute when a
 * campaign fails. A finished sweep left two machines running 86 hours past an
 * expired lease.
 *
 * The lease is the contract: past expiry, an idle machine is reclaimed whether
 * or not anything succeeded. Before expiry it is never touched.
 */
async function reapExpiredLeases(env) {
  const list = await env.RUN_STATE.list({ prefix: "lease/" });
  const now = Date.now();

  for (const key of list.keys) {
    const lease = JSON.parse((await env.RUN_STATE.get(key.name)) ?? "null");
    if (!lease) continue;
    if (now < Date.parse(lease.expires_at)) continue;

    const busy = await computeIsBusy(lease, env);
    if (busy === null) {
      // Cannot read liveness. Hold rather than reclaim: releasing a machine
      // that might be mid-run loses work, and the next tick is 30 minutes away.
      console.warn(`lease ${key.name}: liveness unreadable, holding`);
      continue;
    }
    if (busy) continue;

    await releaseCompute(lease, env);
    await env.RUN_STATE.delete(key.name);
    console.log(`lease ${key.name}: reclaimed`);
  }
}

/* ---- Adapters. Implement these against whatever compute you brought. ---- */

async function dispatchToCompute(_message, _env) {
  throw new Error("dispatchToCompute is not implemented: see ../bring-your-own/");
}

async function computeIsBusy(_lease, _env) {
  // Return true, false, or null when liveness cannot be determined.
  // Never return false as a stand-in for "do not know": that reclaims a
  // machine that may be mid-run.
  return null;
}

async function releaseCompute(_lease, _env) {
  throw new Error("releaseCompute is not implemented: see ../bring-your-own/");
}

/**
 * The feed registry. Fetch it from wherever you keep it, and select on
 * `active`, which means "producing usable signal", not "its process is
 * running". Those are different questions and the difference has cost real
 * data. See ../../contracts/feeds.schema.json.
 */
async function loadActiveFeeds(env) {
  const obj = await env.LAKE.get("config/feeds.json");
  if (!obj) throw new Error("feed registry not found at config/feeds.json");
  const registry = await obj.json();
  return registry.feeds
    .filter((f) => f.active)
    .map((f) => ({ feed: f.feed, camera: f.camera, models: f.models ?? [] }));
}

/* ---- Path contract. Keep ONE implementation. See contracts/lake-path.md. ---- */

function dayPrefix(day) {
  const [y, m, d] = day.split("-");
  return `yyyy=${y}/mm=${m}/dd=${d}/`;
}

function utcDayOffset(days) {
  const t = new Date(Date.now() + days * 86400000);
  return t.toISOString().slice(0, 10);
}

function nowIso() {
  return new Date().toISOString();
}
