# Azure: the reference deployment

What Cascadia Listening Post runs on today.

What the system this documentation describes actually runs on, as a shape rather than an
inventory. Every identifier is a parameter; none are recorded here.

Read this for the reasoning, not as a script to run. If you are starting fresh,
[../cloudflare/](../cloudflare/) is the more complete worked example.

## Resources

| Purpose | Service | Notes |
|---|---|---|
| Media lake | Storage account, ADLS Gen2 | Hierarchical namespace on; the system of record |
| Capture host | One general-purpose VM | Runs every bridge under systemd |
| Secrets | Key Vault | Rendered to environment files on the host |
| Inference | VMs created per campaign | Destroyed on lease expiry |
| Logs and alerts | Log Analytics, Monitor, an action group | See the warning below |
| Scheduling | Automation account, or a host timer | See the warning below |

## Provisioning shape

```sh
# Every value is required. No defaults: a deploy script with a real account
# name as a fallback is how one deployment's identifiers reach another estate.
: "${RESOURCE_GROUP:?}" "${LOCATION:?}" "${LAKE_ACCOUNT:?}" "${LAKE_CONTAINER:?}"

az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

az storage account create \
  --name "$LAKE_ACCOUNT" --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" --sku Standard_LRS --kind StorageV2 \
  --enable-hierarchical-namespace true --min-tls-version TLS1_2 \
  --allow-blob-public-access false

az storage container create \
  --name "$LAKE_CONTAINER" --account-name "$LAKE_ACCOUNT" --auth-mode login
```

Lifecycle: cool at 30 days, archive at 90, **no delete rule**. The archive is the system of
record and holds recordings that cannot be remade.

## Two warnings from this deployment

**The identity path may be blocked, and you should find out early.** Creating role assignments
requires permissions that a Contributor does not have. In the reference deployment no managed
identity has a single role assignment, so the event-driven ingest path and the scheduled
runbooks have never run, and everything authenticates with storage account keys instead.

If your account cannot grant role assignments, discover it on day one rather than after
building around managed identity. Key Vault access policies are set through the Key Vault
resource provider rather than the authorization provider, so switching a vault off role-based
access control is one thing a Contributor can still do.

**Alert rules must split per service.** A scheduled-query rule that aggregates every service
into one condition will fire once, stay fired while any one service is down, and deduplicate
every subsequent failure of every other service. In the reference deployment one stuck alert
made the entire alerting layer inert for fourteen days: six rules enabled, an action group with
a live receiver, eight matching rows, and no notification for any failure.

Split on the service dimension so each gets its own alert instance, explicitly suppress
known-dark nodes so they stop holding a condition open, and add a rule that fires when any
instance has been active beyond a threshold. That last rule is the dead man for the dead man.

## What not to copy

The event-driven consumer and the scheduled runbooks are provisioned and have never run. See
[../../LIMITATIONS.md](../../LIMITATIONS.md). Build the intended orchestration properly rather
than inheriting either the dead path or the host timer that replaced it.

## Cost envelope

The dominant line is inference compute, and only when it is left running. A 16-core VM is
roughly $0.77 an hour, which is about $560 a month idle. Storage tiering handles the lake.
Everything else is noise by comparison.

That single number is the argument for the teardown rule in
[../bring-your-own/](../bring-your-own/).
