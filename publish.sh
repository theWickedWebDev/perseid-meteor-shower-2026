#!/bin/bash
# Hourly: grab a webcam frame, refresh the forecast if there's a new one, rebuild the
# pages, publish if anything moved.
set -u
cd /home/stephen/pittsburg-trip || exit 1
PY=/usr/bin/python3

$PY webcam.py

# Satellite needs h5py, which lives in venv/ rather than system Python. If the venv is
# missing the rest of the run still works - the page falls back to webcam-only ground
# truth and says so.
VENV=/home/stephen/pittsburg-trip/venv/bin/python
if [ -x "$VENV" ]; then
    $VENV satellite.py || echo "$(date '+%F %T')  satellite read failed - continuing"
else
    echo "$(date '+%F %T')  no venv, skipping satellite (python3 -m venv venv && venv/bin/pip install h5py numpy)"
fi

# log_forecast rebuilds the pages on both paths (new data, or no new data). If it fails
# outright — an API down, no network — rebuild from the stored history anyway, so a fresh
# webcam frame still gets rendered instead of being committed but not shown.
if ! $PY log_forecast.py; then
    echo "$(date '+%F %T')  log_forecast failed — rebuilding pages from stored history"
    $PY - <<'EOF' || echo "  fallback rebuild failed too"
import json, os, log_forecast as lf
h = json.load(open(lf.HIST)) if os.path.exists(lf.HIST) else []
if h:                      # write_page does hist[-1]; an empty list is an IndexError
    lf.write_page(h); lf.write_log(h)
else:
    print("  no stored history to rebuild from")
EOF
fi

$PY preview_forecast.py >/dev/null 2>&1 || true   # mock preview, gitignored

if [ -z "$(git status --porcelain)" ]; then
    echo "$(date '+%F %T')  no changes"
    exit 0
fi

git add -A
git commit -q -m "auto: $(date '+%F %H:%M')" || exit 0
git pull -q --rebase origin main 2>&1 || {
    echo "$(date '+%F %T')  rebase failed — resolve by hand"; exit 1; }
git push -q origin main && echo "$(date '+%F %T')  published"
