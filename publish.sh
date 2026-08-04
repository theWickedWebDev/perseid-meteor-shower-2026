#!/bin/bash
# Snapshot the forecast and publish to GitHub Pages, but only when something changed.
# Called from cron. Safe to run manually.
set -u
cd /home/stephen/pittsburg-trip || exit 1

/usr/bin/python3 log_forecast.py

# nothing to do if the logger found no new forecast
if [ -z "$(git status --porcelain)" ]; then
    echo "$(date '+%F %T')  no changes"
    exit 0
fi

git add -A
git commit -q -m "forecast: $(date '+%F %H:%M')" || exit 0

# rebase on anything pushed from elsewhere so a manual edit doesn't cause a conflict loop
git pull -q --rebase origin main 2>&1 || {
    echo "$(date '+%F %T')  pull --rebase failed — resolve by hand"; exit 1; }

git push -q origin main && echo "$(date '+%F %T')  published"
