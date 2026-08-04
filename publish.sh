#!/bin/bash
# Hourly: grab a webcam frame, refresh the forecast if there's a new one, publish if anything moved.
set -u
cd /home/stephen/pittsburg-trip || exit 1

/usr/bin/python3 webcam.py
/usr/bin/python3 log_forecast.py
/usr/bin/python3 preview_forecast.py >/dev/null   # keep the mock preview in step (gitignored)

if [ -z "$(git status --porcelain)" ]; then
    echo "$(date '+%F %T')  no changes"
    exit 0
fi

git add -A
git commit -q -m "auto: $(date '+%F %H:%M')" || exit 0
git pull -q --rebase origin main 2>&1 || {
    echo "$(date '+%F %T')  rebase failed — resolve by hand"; exit 1; }
git push -q origin main && echo "$(date '+%F %T')  published"
