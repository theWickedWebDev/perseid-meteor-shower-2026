#!/usr/bin/env python3
"""
Render FORECAST_FINDINGS.md as findings.html, styled like the rest of the site.

    python3 make_findings.py

The footer of forecast.html linked straight at the .md file, which GitHub Pages either
404s or hands over as raw text. Relying on Jekyll to render it would work but silently —
this way the page carries the same tokens, the same fonts and the same theme toggle as
everything else, and it is obvious when it breaks.

Deliberately not a general Markdown implementation. It handles exactly what the document
uses: headings, tables, fenced code, blockquotes, bullets, rules, links, inline code, bold
and italic. Anything else would pass through untouched, which is the honest failure mode
for a converter with one input file.
"""

import html
import os
import re
import sys
from datetime import datetime, timedelta, timezone

SRC = "FORECAST_FINDINGS.md"
OUT = "findings.html"

# Short anchors the forecast page links to, keyed on the section number so they survive a
# heading being reworded. Add a line here when a new link-out appears on the forecast page.
SHORT = {
    "1-": "ensemble",
    "2-": "trip-probability",
    "3-": "climatology",
    "4-": "waiting",
    "5-": "ground-truth",
    "6-": "where",
    "7-": "fog",
    "9-": "weak",
    "10-": "daytime",
    "11-": "smoke",
}
EDT = timezone(timedelta(hours=-4))


def inline(t):
    """Inline spans.

    Code is pulled out to placeholders rather than split on, so its contents are never
    re-parsed as emphasis AND emphasis can still span it. Splitting first meant that
    `**\u0060EDT\u0060 is fixed at UTC-4**` — bold wrapping a code span — put the two
    asterisk pairs in different segments, so neither found its partner and both were
    printed literally.
    """
    stash = []

    def keep(m):
        stash.append(m.group(1))
        return f"\x00{len(stash) - 1}\x00"

    t = re.sub(r'`([^`]+)`', keep, t)
    t = html.escape(t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    return re.sub(r'\x00(\d+)\x00',
                  lambda m: f'<code>{html.escape(stash[int(m.group(1))])}</code>', t)


def convert(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):                      # fenced code
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i])); i += 1
            i += 1
            out.append('<div class="scroll"><pre>' + "\n".join(buf) + '</pre></div>')
            continue

        if re.match(r'^\|', ln):                      # table
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            body = [c for c in cells if not all(re.fullmatch(r':?-{2,}:?', x or '-') for x in c)]
            head = body[0] if len(body) > 1 and len(cells) > 1 and cells[1] is not body[0] else None
            # a header row exists only if the second source row was the ---- separator
            has_head = len(cells) > 1 and all(
                re.fullmatch(r':?-{2,}:?', x) for x in cells[1])
            t = ['<div class="scroll"><table>']
            if has_head:
                t.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells[0])
                         + "</tr></thead>")
                body = cells[2:]
            else:
                body = cells
            t.append("<tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        if ln.startswith("> "):                       # blockquote
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip()); i += 1
            out.append(f'<blockquote>{inline(" ".join(buf))}</blockquote>')
            continue

        if ln.startswith("- "):                       # bullets
            buf = []
            while i < len(lines) and (lines[i].startswith("- ") or
                                      (buf and lines[i].startswith("  ") and lines[i].strip())):
                if lines[i].startswith("- "):
                    buf.append(lines[i][2:])
                else:
                    buf[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ul>")
            continue

        m = re.match(r'^(#{1,3}) (.*)', ln)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2)
            slug = re.sub(r'[^a-z0-9]+', '-', txt.lower()).strip('-')
            # forecast.html links here by short, stable names. Slugs are derived from the
            # heading text, so rewording a heading silently breaks every inbound link — and
            # a dead anchor just dumps the reader at the top of a long page with no sign
            # anything went wrong. The alias is matched on the section number, which does
            # not change when the wording does.
            alias = next((v for k, v in SHORT.items() if slug.startswith(k)), None)
            anchor = f'<span id="{alias}"></span>' if alias else ''
            out.append(f'{anchor}<h{lvl} id="{slug}">{inline(txt)}</h{lvl}>')
            i += 1
            continue

        if re.fullmatch(r'-{3,}', ln.strip()):
            out.append("<hr>"); i += 1; continue

        if not ln.strip():
            i += 1; continue

        buf = []                                       # paragraph
        while i < len(lines) and lines[i].strip() and not re.match(
                r'^(#{1,3} |\||```|> |- |-{3,}$)', lines[i]):
            buf.append(lines[i]); i += 1
        out.append(f'<p>{inline(" ".join(buf))}</p>')
    return "\n".join(out)


def toc(md):
    items = []
    for m in re.finditer(r'^## (.*)', md, re.M):
        t = m.group(1)
        slug = re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
        items.append(f'<a href="#{slug}">{html.escape(t)}</a>')
    return '<nav class="toc">' + "".join(items) + '</nav>'


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>How these numbers are made · Pittsburg Aug 11–14</title>
<meta name="color-scheme" content="dark light">
<style>
:root{{
  --ground:#F1F3F7; --surface:#FFFFFF; --ink:#171C26; --body:#3B4453; --muted:#6C7789;
  --rule:#D3D9E4; --accent:#B5721A; --good:#2E6B4F; --warn:#B5721A; --bad:#B03A2C;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
  --serif:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
}}
@media (prefers-color-scheme:dark){{:root{{
  --ground:#0A0D14; --surface:#121722; --ink:#E7ECF5; --body:#BAC4D4; --muted:#7A8698;
  --rule:#232B39; --accent:#E3A445; --good:#6FBF95; --warn:#E3A445; --bad:#E8705C;
}}}}
:root[data-theme="light"]{{
  --ground:#F1F3F7; --surface:#FFFFFF; --ink:#171C26; --body:#3B4453; --muted:#6C7789;
  --rule:#D3D9E4; --accent:#B5721A; --good:#2E6B4F; --warn:#B5721A; --bad:#B03A2C;
}}
:root[data-theme="dark"]{{
  --ground:#0A0D14; --surface:#121722; --ink:#E7ECF5; --body:#BAC4D4; --muted:#7A8698;
  --rule:#232B39; --accent:#E3A445; --good:#6FBF95; --warn:#E3A445; --bad:#E8705C;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--body);font-family:var(--sans);
  line-height:1.65;padding-bottom:4rem}}
.wrap{{max-width:46rem;margin:0 auto;padding:0 clamp(1rem,3.5vw,1.6rem)}}
.bar{{position:sticky;top:0;z-index:9;background:var(--ground);
  border-bottom:1px solid var(--rule)}}
.bar-in{{max-width:46rem;margin:0 auto;padding:.5rem clamp(1rem,3.5vw,1.6rem);
  display:flex;gap:.6rem;align-items:center}}
.bar a{{font-family:var(--mono);font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);text-decoration:none}}
.bar a:hover{{color:var(--accent)}}
.bar .sp{{margin-right:auto}}
.btn{{font-family:var(--mono);font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;
  background:transparent;color:var(--body);border:1px solid var(--rule);padding:.4rem .65rem;
  border-radius:3px;cursor:pointer}}
.btn:hover{{border-color:var(--accent);color:var(--accent)}}
h1{{font-family:var(--serif);color:var(--ink);font-size:clamp(1.5rem,5vw,2.1rem);
  margin:2rem 0 .4rem;line-height:1.15}}
h2{{font-family:var(--serif);color:var(--ink);font-size:1.25rem;margin:2.6rem 0 .7rem;
  padding-top:.4rem}}
h3{{font-family:var(--serif);color:var(--ink);font-size:1.02rem;margin:1.8rem 0 .5rem}}
p{{margin:.7rem 0}}
a{{color:var(--accent)}}
b{{color:var(--ink)}}
code{{font-family:var(--mono);font-size:.86em;background:var(--surface);
  border:1px solid var(--rule);border-radius:3px;padding:.05rem .3rem}}
pre{{font-family:var(--mono);font-size:.78rem;line-height:1.5;background:var(--surface);
  border:1px solid var(--rule);border-radius:4px;padding:.8rem 1rem;margin:.9rem 0;
  color:var(--ink);overflow-x:auto}}
pre code{{background:none;border:0;padding:0}}
blockquote{{margin:1rem 0;padding:.7rem .9rem;border-left:2px solid var(--accent);
  background:var(--surface);border-radius:0 3px 3px 0;color:var(--body)}}
table{{border-collapse:collapse;width:100%;font-size:.9rem;margin:.9rem 0}}
th,td{{text-align:left;padding:.45rem .6rem;border-bottom:1px solid var(--rule);
  vertical-align:top}}
th{{font-family:var(--mono);font-size:.64rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted)}}
ul{{margin:.8rem 0;padding-left:1.1rem}}
li{{margin:.45rem 0}}
hr{{border:0;border-top:1px solid var(--rule);margin:2rem 0}}
.scroll{{overflow-x:auto}}
.toc{{display:flex;flex-direction:column;gap:.25rem;background:var(--surface);
  border:1px solid var(--rule);border-radius:4px;padding:.9rem 1.1rem;margin:1.4rem 0}}
.toc a{{font-size:.86rem;text-decoration:none;color:var(--body)}}
.toc a:hover{{color:var(--accent)}}
.foot{{margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--rule);
  color:var(--muted);font-size:.84rem}}
</style>
</head>
<body>
<div class="bar"><div class="bar-in">
  <a href="forecast.html">← Forecast</a>
  <a href="index.html" class="sp">Trip plan</a>
  <button class="btn" id="theme">Theme</button>
</div></div>
<div class="wrap">
{toc}
{body}
<div class="foot">
  <a href="forecast.html">← Back to the forecast</a> ·
  generated from <span style="font-family:var(--mono)">FORECAST_FINDINGS.md</span>,
  last edited {stamp} EDT
</div>
</div>
<script>
(function(){{
  var r=document.documentElement,t=document.getElementById('theme');
  var s=localStorage.getItem('theme'); if(s) r.setAttribute('data-theme',s);
  t.addEventListener('click',function(){{
    var cur=r.getAttribute('data-theme');
    if(!cur) cur=matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';
    var nx=cur==='dark'?'light':'dark';
    r.setAttribute('data-theme',nx); localStorage.setItem('theme',nx);
  }});
}})();
</script>
</body>
</html>
"""


def main():
    md = open(SRC).read()
    title = re.match(r'^# (.*)', md).group(1) if md.startswith("# ") else "Findings"
    body = convert(md)
    # Stamp the SOURCE, not the build. Using the clock meant regenerating with no content
    # change produced a one-line diff, and on a fresh clone — where checkout resets both
    # mtimes — publish.sh's -nt guard could fire arbitrarily and commit that no-op.
    src_mtime = datetime.fromtimestamp(os.path.getmtime(SRC), EDT)
    page = PAGE.format(toc=toc(md), body=body,
                       stamp=f"{src_mtime:%a %d %b %Y, %H:%M}")
    open(OUT, "w").write(page)
    print(f"wrote {OUT} — {len(page)//1024} KB from {SRC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
