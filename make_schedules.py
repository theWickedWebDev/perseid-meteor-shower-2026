#!/usr/bin/env python3
"""
Regenerate the timeline tables in SCHEDULE_3_NIGHTS.md from schedule_data.py, so the
markdown and pittsburg-2026.ics cannot disagree.

    python3 make_schedules.py            # rewrite the tables
    python3 make_schedules.py --check    # report drift, change nothing

Only the tables between the GENERATED markers are touched. Every hand-written section
around them — the shape-of-the-night notes, the porch reasoning, the kit lists, the
standing notes — is left exactly as written.

--check also scans the hand-written contingency plans (SCHEDULE_1_NIGHT.md,
SCHEDULE_2_NIGHTS.md and the rest) for astronomical times that no longer match the
ephemeris. Those are separate plans rather than subsets of this one, so they are reported
and never rewritten.
"""

import re
import sys
import pathlib
from datetime import datetime

import schedule_data as sd

TARGET = "SCHEDULE_3_NIGHTS.md"
BACKUP = ".schedule_backup"

NIGHTS = [("NIGHT 1", sd.NIGHT1), ("NIGHT 2", sd.NIGHT2), ("NIGHT 3", sd.NIGHT3)]

BEGIN = "<!-- GENERATED FROM schedule_data.py — edit there, then run make_schedules.py -->"
END = "<!-- END GENERATED -->"


def hr12(hhmm):
    """'17:00' -> '5:00 PM'. Only the boundary rows carry the meridiem."""
    h, m = map(int, hhmm.split(":"))
    return f"{(h % 12) or 12}:{m:02d}", ("AM" if h < 12 else "PM")


def table(events):
    """One night as a markdown table. Bold the time, lead with the summary."""
    rows = ["| Time | Action |", "|---|---|"]
    last_mer = None
    for ev in sorted(events, key=lambda e: (e[0], e[1])):
        day, hhmm, _alarm, summary, desc = ev[:5]
        md = ev[5] if len(ev) > 5 else None
        t, mer = hr12(hhmm)
        # show AM/PM only when it changes, so the column stays scannable
        stamp = f"{t} {mer}" if mer != last_mer else t
        last_mer = mer
        body = md or f"**{summary}** {desc}"
        body = body.replace("|", "\\|").replace("\n", " ")
        body = re.sub(r"\s+", " ", body).strip()
        rows.append(f"| **{stamp}** | {body} |")
    return "\n".join(rows)


def block(label, events):
    return f"{BEGIN}\n\n{table(events)}\n\n{END}"


def rewrite(text, check=False):
    """Replace each night's table in place. Returns (new_text, [changed labels])."""
    changed = []
    for label, events in NIGHTS:
        want = block(label, events)
        # the night section runs from its heading to the next top-level heading
        m = re.search(rf"^# {re.escape(label)}\b.*?$", text, re.M)
        if not m:
            changed.append(f"{label}: heading not found")
            continue
        start = m.end()
        nxt = re.search(r"^# ", text[start:], re.M)
        end = start + (nxt.start() if nxt else len(text) - start)
        section = text[start:end]

        existing = re.search(rf"{re.escape(BEGIN)}.*?{re.escape(END)}", section, re.S)
        if existing:
            if existing.group(0).strip() == want.strip():
                continue
            new_section = section[:existing.start()] + want + section[existing.end():]
        else:
            # first run: swap the hand-written table for the generated block
            tbl = re.search(r"^\| Time \| Action \|\n\|-+\|-+\|\n(?:\|.*\n)+", section, re.M)
            if not tbl:
                changed.append(f"{label}: no table found")
                continue
            new_section = section[:tbl.start()] + want + "\n" + section[tbl.end():]
        changed.append(label)
        if not check:
            text = text[:start] + new_section + text[end:]
    return text, changed


# Only lines that ASSERT a deadline are checked. Altitude tables and target windows
# legitimately quote all sorts of times; flagging those buries the real drift in noise.
CLAIMS = [
    (re.compile(r"core deadline|hard deadline|core at 10|core is up|southern window"
                r"|core window", re.I), "core_set"),
    (re.compile(r"rho oph deadline|rho.{0,12}deadline", re.I), "rho_set"),
    (re.compile(r"astronomical dark|dark starts", re.I), "dark"),
]


def check_astro():
    """Deadline claims in the docs that no longer match the ephemeris."""
    bad = [f"schedule_data.ASTRO is stale — {s}" for s in sd._verify_astro()]
    ok = {k: {hr12(a[k])[0] for a in sd.ASTRO.values()} for k in ("core_set", "rho_set", "dark")}
    for f in sorted(pathlib.Path(".").glob("*.md")):
        for n, line in enumerate(f.read_text().split("\n"), 1):
            for rx, key in CLAIMS:
                if not rx.search(line):
                    continue
                # prose about transits, spans and per-night drift legitimately names other
                # times; only assertions of the deadline itself are interesting
                if re.search(r"transit|between|per night|earlier per|Aug 14"
                             r"|deadline isn't|deadline is not", line, re.I):
                    continue
                # A line may legitimately quote a range ("9:54 - 11:17") or a lead-in time.
                # Only complain when NOTHING on the line matches the ephemeris.
                times = re.findall(r"\b(\d{1,2}:[0-5]\d)\b", line)
                if times and not (set(times) & ok[key]):
                    bad.append(f"{f}:{n} claims {key.replace('_', ' ')} at "
                               f"{', '.join(times)} — ephemeris says "
                               f"{'/'.join(sorted(ok[key]))}")
    return bad


def main():
    check = "--check" in sys.argv
    p = pathlib.Path(TARGET)
    text = p.read_text()

    if not check:
        b = pathlib.Path(BACKUP)
        b.mkdir(exist_ok=True)
        stamp = max([0] + [int(x.stem.split("-")[-1]) for x in b.glob("*.md")]) + 1
        (b / f"{p.stem}-{stamp}.md").write_text(text)

    new, changed = rewrite(text, check=check)
    if check:
        print(f"{TARGET}: {'would rewrite ' + ', '.join(changed) if changed else 'up to date'}")
        for line in check_astro():
            print(f"  DRIFT  {line}")
        return

    if new != text:
        p.write_text(new)
    print(f"wrote {TARGET}: {', '.join(changed) if changed else 'no change'}")
    for line in check_astro():
        print(f"  DRIFT  {line}")


if __name__ == "__main__":
    main()
