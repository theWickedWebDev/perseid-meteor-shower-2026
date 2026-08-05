#!/bin/bash
# One nightwatch capture, dark hours only. Called from cron every 15 min.
cd /home/stephen/pittsburg-trip || exit 1

# One capture at a time. A hung grab can run to its 210 s timeout, which is longer than the
# 15 min cron gap only in the worst case, but concurrent yt-dlp/ffmpeg pairs are pointless
# and the stack would be built from a half-written directory.
exec 9>/tmp/.nightwatch.lock
flock -n 9 || exit 0
H=$(date +%H)
if [ "$H" -ge 5 ] && [ "$H" -lt 20 ]; then exit 0; fi
exec ./venv/bin/python -u nightwatch.py --once
