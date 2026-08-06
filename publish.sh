#!/bin/bash
# Hourly: grab a webcam frame, refresh the forecast if there's a new one, rebuild the
# pages, publish if anything moved.
set -u
cd /home/stephen/pittsburg-trip || exit 1
PY=/usr/bin/python3

# Climatology and lead-time skill: thirty archive calls plus seven previous-run calls,
# and neither moves hourly. Refresh once a day, and never let it block the run.
if [ ! -f skill.json ] || [ -n "$(find skill.json -mmin +1200 2>/dev/null)" ]; then
    $PY skill.py >/dev/null 2>&1 || echo "$(date '+%F %T')  skill refresh failed - using cache"
fi

$PY webcam.py

# Satellite needs h5py, which lives in venv/ rather than system Python. If the venv is
# missing the rest of the run still works - the page falls back to webcam-only ground
# truth and says so.
VENV=/home/stephen/pittsburg-trip/venv/bin/python
if [ -x "$VENV" ]; then
    $VENV satellite.py || echo "$(date '+%F %T')  satellite read failed - continuing"

# Close any hole a dropped connection left. GOES keeps granules for months, so an
# hour missed overnight can still be recovered — and those are the dark hours every
# model is scored against, so losing them quietly biases the scorecard.
python3 backfill_satellite.py --write --since "$(date -d '2 days ago' +%Y-%m-%dT%H:00)" >/dev/null 2>&1 || true

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

# findings.html is generated from the markdown; regenerate when the source is newer
# Regenerate unconditionally: the output is now a pure function of the source, so a
# rebuild that changes nothing writes identical bytes and git sees no diff. An mtime guard
# was wrong on a fresh clone, where checkout gives every file the same timestamp.
# Build the full-resolution sky mask once, in daylight, from the rendition nightwatch
# actually analyses. The fallback mask is upscaled from 760 px and approximate at the
# treeline, which is exactly where false stars would creep in.
if [ ! -f skymask_hd.npy ] && [ -x venv/bin/python ]; then
    H=$(date +%H)
    if [ "$H" -ge 10 ] && [ "$H" -lt 17 ]; then
        ./venv/bin/python nightwatch.py --build-mask 2>&1 | sed 's/^/  /' || true
    fi
fi

$PY inject_cards.py >/dev/null 2>&1 || true   # live cards at the top of the trip plan
$PY make_nightwatch.py >/dev/null 2>&1 || true   # star-count evidence page
$PY make_findings.py >/dev/null || echo "$(date '+%F %T')  findings render failed"

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

# desktop popup only when the headline number actually moves — see notify_trip.py
$PY notify_trip.py || true
