#!/usr/bin/env bash
# Everything that can be checked without an account. Run before publishing.
set -Eeuo pipefail

cd "$(dirname "$0")/.."
PY="${PYTHON_BIN:-python3}"
fail=0
step() { printf '\n== %s\n' "$1"; }

step "Redaction"
$PY tools/check_redaction.py . --explain || fail=1

step "Redaction rules still catch real leaks"
$PY tools/test_redaction.py || fail=1

step "Schemas are valid, and match published data where available"
$PY tools/validate_schemas.py || fail=1

step "Shell and JavaScript parse"
n=0
for f in $(find . -name '*.sh' -not -path './.git/*'); do
  bash -n "$f" || fail=1
  n=$((n + 1))
done
echo "   $n shell script(s) parsed"
if command -v node >/dev/null; then
  n=0
  for f in $(find deploy -name '*.js' -not -path '*/node_modules/*'); do
    node --check "$f" || fail=1
    n=$((n + 1))
  done
  echo "   $n JavaScript file(s) parsed"
else
  echo "   node not present, skipping JavaScript check"
fi

step "No em-dashes in prose"
if grep -rn '—' --include='*.md' . ; then
  echo "   em-dashes found above"; fail=1
else
  echo "   clean"
fi

step "Relative links resolve"
$PY - <<'PYCHECK' || fail=1
import re, pathlib, sys
missing = []
for md in sorted(pathlib.Path(".").rglob("*.md")):
    if ".git" in md.parts:
        continue
    for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", md.read_text()):
        t = m.group(1)
        if t.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = t.split("#")[0]
        if target and not (md.parent / target).resolve().exists():
            missing.append(f"{md}: {t}")
print(f"   broken relative links: {len(missing)}")
for x in missing:
    print("   ", x)
sys.exit(1 if missing else 0)
PYCHECK

printf '\n%s\n' "$( [ "$fail" -eq 0 ] && echo 'verify: all checks passed' || echo 'verify: FAILURES above' )"
exit "$fail"
