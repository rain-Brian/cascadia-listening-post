#!/usr/bin/env python3
"""Refuse to publish anything carrying infrastructure detail.

A content scan over a finished tree, run immediately before it becomes public.
The leak that matters is the one nobody meant to write, so this checks the
artifact rather than trusting the process that produced it.

Standalone: no dependencies, no configuration file. Adapt HOST_PREFIXES to your
own naming, because a pattern matching somebody else's estate protects nothing.

    python3 tools/check_redaction.py .
    python3 tools/check_redaction.py . --explain
    python3 tools/check_redaction.py . --allow 'some-literal-string'

Exit 0 clean, 1 findings, 2 bad usage.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Text worth scanning. Media is skipped: an image cannot leak a hostname in a
# form these patterns catch, and scanning base64 for GUID-shaped runs produces
# only false positives.
TEXT_SUFFIXES = {
    ".html", ".htm", ".json", ".jsonc", ".js", ".ts", ".css", ".csv", ".md",
    ".txt", ".xml", ".svg", ".yaml", ".yml", ".toml", ".sh", ".py", ".ps1", ".cff",
}

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".wrangler"}

# Adapt this to your own deployment naming.
HOST_PREFIXES = r"vm-|host-"
DEPLOY_ROOTS = r"/(?:opt|etc|srv)/[a-z][\w-]*bridges"
VAULT_PREFIXES = r"kv-"

RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("vm_hostname", re.compile(rf"\b(?:{HOST_PREFIXES})[\w.-]*\b"),
     "a host name, which names a machine to attack"),
    ("deploy_path", re.compile(rf"{DEPLOY_ROOTS}[\w./-]*"),
     "the deployment layout on a host"),
    ("key_vault", re.compile(rf"\b(?:{VAULT_PREFIXES})[\w-]*\b"),
     "the secret store holding every runtime credential"),
    ("storage_account", re.compile(r"\bst\d{6,}\w*\b"),
     "the object store account name"),
    ("systemd_unit", re.compile(r"\b[\w-]+\.(?:service|timer)\b"),
     "a service unit name, which maps the capture tier"),
    ("sas_token", re.compile(r"[?&](?:sig|sv|se|sp)=[^\s\"'&<]+"),
     "a signed URL parameter, which is a live credential"),
    ("account_key", re.compile(r"AccountKey=[^\s;\"'<]+"),
     "a storage account key"),
    ("connection_string", re.compile(r"DefaultEndpointsProtocol=[^\s\"'<]+"),
     "a storage connection string"),
    ("guid", re.compile(r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b"),
     "a subscription, tenant or principal identifier"),
    ("operator_home", re.compile(r"/(?:Users|home)/(?!<)[\w.-]+/"),
     "an operator's home directory, which names a person and a machine"),
    ("private_ip", re.compile(
        r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
     "a private network address"),
    # Not in the implementation this is modelled on, and its absence is a real
    # gap: a deploy script is exactly where a reachable address gets hardcoded.
    ("public_ip", re.compile(
        r"(?<![\w.])(?!0\.|127\.|10\.|169\.254\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)"
        r"(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?![\w.])"),
     "a public address, which names a reachable host"),
    # Deliberately narrower than "any uppercase assignment". That broader form
    # is right for a report bundle, where no assignment is expected at all, but
    # in a deployment repository it fires on every LAKE="$PREFIX-lake" and the
    # noise buries the one line that matters. This targets the rule's actual
    # purpose: a secret-shaped NAME bound to a literal value. A value that is a
    # variable expansion, a placeholder or empty is carrying nothing.
    ("env_assignment", re.compile(
        r"^\s*(?:export\s+)?[A-Z][A-Z0-9_]*"
        r"(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|SAS|CREDENTIAL|CONN(?:ECTION)?)"
        r"[A-Z0-9_]*=(?![\s\n]*$)(?!['\"]?[\$<])['\"]?[^\s'\"]{6,}",
        re.MULTILINE),
     "a secret-shaped environment assignment bound to a literal value"),
    ("bearer_token", re.compile(r"\b(?:Bearer|Authorization:)\s+[\w.\-]{20,}"),
     "an authorization header"),
)


@dataclass(frozen=True)
class Finding:
    rule: str
    leaks: str
    path: Path
    line: int
    excerpt: str


def _excerpt(text: str, start: int, end: int, width: int = 60) -> str:
    """The match with a little context, truncated. A failure report that prints
    the whole key has moved the secret rather than caught it."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    line_end = len(text) if line_end == -1 else line_end
    matched = text[start:end]
    if len(matched) > 24:
        matched = matched[:20] + "..."
    left = text[max(line_start, start - width):start].lstrip()
    right = text[end:min(line_end, end + width)].rstrip()
    return f"{left}>>{matched}<<{right}"


def scan_text(text: str, path: Path, allow: tuple[str, ...]) -> list[Finding]:
    out: list[Finding] = []
    for name, pattern, leaks in RULES:
        for m in pattern.finditer(text):
            if any(a and a in m.group(0) for a in allow):
                continue
            out.append(Finding(
                rule=name, leaks=leaks, path=path,
                line=text.count("\n", 0, m.start()) + 1,
                excerpt=_excerpt(text, m.start(), m.end()),
            ))
    return out


def scan_tree(root: Path, allow: tuple[str, ...]) -> list[Finding]:
    findings: list[Finding] = []
    # This file defines the patterns and its test file exercises them with
    # fabricated leaks, so both match by construction. A scanner that flags its
    # own rule table teaches people to ignore it. Nothing else is exempt, and
    # this is a fixed pair of paths rather than a name pattern, so a file
    # cannot become exempt by being named a certain way.
    here = Path(__file__).resolve().parent
    exempt = {here / "check_redaction.py", here / "test_redaction.py"}
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.resolve() in exempt:
            continue
        if not p.is_file() or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        findings.extend(scan_text(text, p.relative_to(root), allow))
    return findings


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", type=Path, nargs="?", default=Path("."))
    ap.add_argument("--allow", action="append", default=[],
                    help="Allow one specific literal string. Never a rule.")
    ap.add_argument("--explain", action="store_true",
                    help="Group findings by rule with the reason each matters.")
    args = ap.parse_args(argv)

    if not args.root.is_dir():
        print(f"not a directory: {args.root}", file=sys.stderr)
        return 2

    findings = scan_tree(args.root, tuple(args.allow))
    if not findings:
        print(f"redaction: clean ({args.root})")
        return 0

    if args.explain:
        by_rule: dict[str, list[Finding]] = {}
        for f in findings:
            by_rule.setdefault(f.rule, []).append(f)
        for rule, group in sorted(by_rule.items(), key=lambda kv: -len(kv[1])):
            print(f"\n{rule}  ({len(group)}) leaks {group[0].leaks}")
            for f in group[:12]:
                print(f"    {f.path}:{f.line}  {f.excerpt}")
            if len(group) > 12:
                print(f"    ... and {len(group) - 12} more")
    else:
        for f in findings:
            print(f"  {f.path}:{f.line}  [{f.rule}] {f.leaks}\n      {f.excerpt}")

    print(f"\nredaction: {len(findings)} finding(s). "
          f"Resolve each with a placeholder, or allow the specific string. "
          f"Do not disable a rule.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
