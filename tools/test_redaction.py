#!/usr/bin/env python3
"""Assert every redaction rule fires on a real leak and on nothing else.

`env_assignment` is narrower here than in the gate this is modelled on, so the
narrowing is tested rather than trusted. Run this after any rule change:

    python3 tools/test_redaction.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_redaction import RULES, scan_text  # noqa: E402

# One realistic leak per rule. Values are fabricated but shaped like the real
# thing, because a pattern that only matches a tidy example is not a gate.
LEAKS = {
    "vm_hostname":       'HOST=vm-example-prod-01',
    "deploy_path":       'cd /opt/example-bridges/current',
    "key_vault":         'VAULT=kv-example-prod',
    "storage_account":   'account is st00000000examplelake here',
    "systemd_unit":      'systemctl restart example-feed-audio.service',
    "sas_token":         'https://x.example/c?sv=2021-06-08&sig=AbCdEf123456',
    "account_key":       'AccountKey=Zm9vYmFyYmF6cXV1eA==',
    "connection_string": 'DefaultEndpointsProtocol=https;AccountName=x',
    "guid":              'SUB=0f1e2d3c-4b5a-4968-8776-a5b4c3d2e1f0',
    "operator_home":     'ls /Users/somebody/wildlife-runs',
    "private_ip":        'INTERNAL=10.1.2.3',
    "public_ip":         'ssh bridge@203.0.113.57',
    "env_assignment":    'LAKE_STORAGE_KEY=Zm9vYmFyYmF6cXV1eDEyMzQ1',
    "bearer_token":      'curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9xxxxx"',
}

# Legitimate deployment configuration. None of this may fire.
CLEAN = """
LAKE="$CF_PREFIX-lake"
WORK_QUEUE="${CF_PREFIX}-inference-work"
STORAGE_ACCOUNT=<your-account>
API_TOKEN="$(read_secret)"
: "${CF_PREFIX:?CF_PREFIX is required}"
npx wrangler secret put COMPUTE_API_TOKEN
Set CF_PREFIX in your environment, then run setup.sh.
A unit named <feed>-<camera>-audio is supervised by the init system.
Documented at https://developers.cloudflare.com/r2/buckets/object-lifecycles/
"""


def main() -> int:
    failures: list[str] = []
    here = Path("test")

    for rule, _pattern, _leaks in RULES:
        sample = LEAKS.get(rule)
        if sample is None:
            failures.append(f"{rule}: no sample leak defined, rule is untested")
            continue
        fired = {f.rule for f in scan_text(sample, here, ())}
        if rule not in fired:
            failures.append(f"{rule}: did NOT fire on its own leak: {sample!r}")

    for f in scan_text(CLEAN, here, ()):
        failures.append(
            f"{f.rule}: false positive on legitimate config, line {f.line}: {f.excerpt}"
        )

    allowed = scan_text(LEAKS["vm_hostname"], here, ("vm-example-prod-01",))
    if any(f.rule == "vm_hostname" for f in allowed):
        failures.append("--allow did not suppress an explicitly allowed literal")

    if failures:
        print(f"redaction rules: {len(failures)} FAILURE(S)\n")
        for line in failures:
            print(f"  {line}")
        return 1

    print(f"redaction rules: {len(RULES)} rules, each fires on a leak, "
          f"none on legitimate config, --allow honoured. OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
