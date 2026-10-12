#!/usr/bin/env bash
# Step-by-step demo for the recording. Pauses before each step so you can narrate.
#
#   bash demo/run_demo.sh            # interactive: press Enter to advance
#   DEMO_NOPAUSE=1 bash demo/run_demo.sh   # run straight through (rehearsal / check)
#
# Matches the scenes in RECORDING_SCRIPT.md. The bug demo (scene 2) writes to a temp
# folder. The live run (scene 3) regenerates reports/2026-09 and reports/2026-07 with
# the same results that are committed.
set -euo pipefail
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

step() {
  printf '\n\033[1m=== %s ===\033[0m\n' "$1"
  if [ -z "${DEMO_NOPAUSE:-}" ]; then read -r -p "(Enter to run) " _; fi
}

step "Scene 1 · One commit per prompt"
git log --oneline -- . | cat

step "Scene 2a · Build an extract with 150 claims from a ZIP3 the reference table does not know"
python3 demo/make_unmapped_extract.py "$TMP/claims_unmapped.csv"

step "Scene 2b · BEFORE: the analyzer as first built (commit 37259c6)"
git show 37259c6:halcyon-model-monitoring/analyzer.py > "$TMP/analyzer_before_fix.py"
PYTHONPATH=. python3 "$TMP/analyzer_before_fix.py" --claims "$TMP/claims_unmapped.csv" --out-dir "$TMP/before" | head -2
echo "Summary header says:"
grep -o "[0-9,]* claims  ·" "$TMP/before/flag_summary_2026-09.md"
echo "Claims actually in the file for 2026-09:"
python3 -c "import pandas as pd; print(f\"{(pd.read_csv('$TMP/claims_unmapped.csv')['month']=='2026-09').sum():,}\")"

step "Scene 2c · AFTER: the current analyzer on the same file"
python3 analyzer.py --claims "$TMP/claims_unmapped.csv" --out-dir "$TMP/after" | head -4 | cut -c1-200

step "Scene 2d · The regression test that keeps it fixed"
python3 -m unittest tests.test_analyzer.Analyzer.test_unmapped_zip_claims_are_reported_not_silently_dropped 2>&1 | tail -3

step "Scene 3a · Full test suite"
python3 -m unittest discover -s tests 2>&1 | tail -3

step "Scene 3b · LIVE RUN: analyzer, September 2026"
python3 analyzer.py

step "Scene 3c · Cross-check with the monitor"
python3 monitor.py

step "Scene 3d · The refresh month: July 2026 against the April-June baseline"
python3 analyzer.py --month 2026-07 | grep -E "tier|Drift" | cut -c1-170

printf '\n\033[1m=== Done. Open reports/2026-09/flag_summary_2026-09.md and the charts next. ===\033[0m\n'
