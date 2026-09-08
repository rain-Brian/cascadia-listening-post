# Security

## Reporting

This repository holds documentation and deployment configuration. It runs nothing and stores no
data.

If you find something here that should not be public, please report it privately rather than
opening an issue. In particular:

- A credential, key, token or signed URL of any kind.
- Infrastructure detail belonging to a real deployment: a hostname, storage account, key vault,
  subscription or tenant identifier, service unit name, internal address or operator path.
- Guidance that would lead a reader to build something insecure.

Contact the repository owner through their GitHub profile.

## What this repository deliberately does not contain

No credentials, no infrastructure identifiers, no model code, no weights. Every name in
`deploy/` is a required parameter or a placeholder.

The absence of infrastructure detail is enforced by a content scan before publication, not by
care alone. See [tools/redact.md](tools/redact.md). A gate catches the patterns it knows about,
which is why a report is still worth sending.

## Security guidance in this documentation

Several practices here exist because their absence caused a real problem. They are worth
following even when they seem fussy:

- Keep secrets off the process table. A long-running process with a credential in its argument
  vector exposes it to any local user for the life of that process.
- Set a restrictive umask before writing rendered configuration, not after.
- Grant a capture user only the specific verbs it needs, never blanket privilege escalation.
- Scan content for secrets in continuous integration, not filenames on demand.
- Give capture credentials that can write the raw zone and nothing else. Capture should not be
  able to delete.

See Layer 7 in [ARCHITECTURE.md](reference/ARCHITECTURE.md).
