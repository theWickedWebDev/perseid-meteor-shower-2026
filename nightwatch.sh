#!/bin/bash
# One nightwatch capture, dark hours only. Called from cron every 15 min.
cd /home/stephen/pittsburg-trip || exit 1
H=$(date +%H)
if [ "$H" -ge 5 ] && [ "$H" -lt 20 ]; then exit 0; fi
exec ./venv/bin/python -u nightwatch.py --once
