# Redaction gate

The rule set that keeps infrastructure detail out of a public artifact, and the reasoning
behind each rule.

`check_redaction.py` in this directory is a standalone implementation. Run it over anything you
are about to make public.

## Why a content scan rather than a rule about how pages are written

The leak that matters is the one nobody meant to write: a run directory path in an error
string, a hostname in a debug comment, a signed URL pasted into a caption. None of those are
things a renderer sets out to emit, so no amount of care in the renderer catches them.

Scan the finished artifact, immediately before it becomes public, while the change is still
local. A public repository cannot be un-published.

## The rules

| Rule | Catches | Why it matters |
|---|---|---|
| `vm_hostname` | Capture host names | Names a machine to attack |
| `deploy_path` | Deployment layout on a host | Maps the estate |
| `key_vault` | Secret store names | Names where every runtime secret lives |
| `storage_account` | Object store account names | Names the lake |
| `systemd_unit` | Service unit names | Maps the capture tier feed by feed |
| `sas_token` | Signed URL parameters | A live credential |
| `account_key` | Storage account keys | A live credential |
| `connection_string` | Connection strings | A live credential |
| `guid` | Subscription, tenant, principal identifiers | Identifies the tenancy |
| `operator_home` | Home directory paths | Names a person and a machine |
| `private_ip` | RFC1918 addresses | Maps the internal network |
| `public_ip` | Bare public IPv4 addresses | Names a reachable host |
| `env_assignment` | Uppercase environment assignments | How secrets travel |
| `bearer_token` | Authorization headers | A live credential |

Adapt the first four to your own naming. They are prefix patterns, and a pattern that matches
somebody else's estate protects nothing.

## Three deliberate differences from the reference implementation

The gate this is modelled on was written to scan finished report bundles. A repository of
deployment configuration is a different artifact, and three things change.

**`public_ip` is added.** The original has no rule for public addresses, because a report bundle
is unlikely to contain one. A deploy script is exactly where a reachable address gets hardcoded:
the reference deployment carries batch machine addresses as a default value in an orchestration
module, and nothing would have caught them.

**Shell and configuration files are scanned.** The original's suffix list covers web and data
formats only, so `.sh`, `.py`, `.ps1`, `.toml`, `.yaml` and `.jsonc` are never opened. A gate
that cannot read a deploy script cannot protect a deploy repository.

**`env_assignment` is narrower.** The original matches any uppercase `NAME=value`. That is right
for a bundle, where no assignment is expected at all, but here it fires on every
`LAKE="$PREFIX-lake"` and the noise buries the one line that matters. This version requires a
secret-shaped name (`KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `SAS`, `CREDENTIAL`, `CONN`) bound to
a literal value, and ignores values that are variable expansions, placeholders or empty, because
those carry nothing.

That third change is a narrowing, so it is tested rather than trusted: `test_redaction.py`
asserts every rule still fires on a file of realistic leaks, and that none fires on legitimate
deployment configuration. Run it after any rule change.

## Scan text, skip media

Text suffixes only. An image cannot leak a hostname in a form these patterns catch, and
scanning megabytes of base64 for GUID-shaped runs produces only false positives.

## Overrides take a string, never a rule

An override allows one specific literal. It never disables a rule.

Record every override in the published artifact itself, so it is visible to a reader rather
than living only in somebody's shell history.

## Expect false positives in a documentation repository, and do not silence them

Two rules fire on legitimate content here:

- **`env_assignment`** matches every `NAME=value` example, and a deployment guide needs those.
- **`systemd_unit`** matches any prose naming a unit file, and the capture tier runs under one.

The fix is to write examples with placeholders (`<your-account>`, `<feed>-<camera>.service`) so
the rules pass honestly, or to allow the specific literal string. Turning a rule off in a
repository whose whole purpose is describing infrastructure is exactly backwards: this is the
repository where the rule earns its keep.

`check_redaction.py --explain` lists what fired and why, so a human can judge each one.
