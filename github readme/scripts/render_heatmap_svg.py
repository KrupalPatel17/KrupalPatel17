#!/usr/bin/env python3
"""
Render data/contributions.json (written by fetch_contributions.py) as an
animated GitHub-style contribution heatmap SVG: the classic 53-week x 7-day
grid of rounded squares, each popping in once with a diagonal sweep (CSS
keyframes play on load, then freeze). GitHub runs CSS animations inside SVGs
embedded with <img>, so no JavaScript is involved.

    python scripts/render_heatmap_svg.py [data/contributions.json] [contrib-heatmap.svg]

Approach adapted from https://github.com/AVIVASHISHTA29/AVIVASHISHTA29
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "contrib-heatmap.svg")

# ---- layout ---------------------------------------------------------------
CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.5, 34, 24
STEP = CELL + GAP
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]  # GitHub levels 0..4
GRAY = "#7d8590"
INK = "#e6edf3"

# ---- timing (seconds) -----------------------------------------------------
REVEAL, DUR = 3.6, 0.55

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)
days = data["days"]
total = data["total_contributions"]

# Lay the days out in calendar columns: one column per week, Sunday on top.
# The first column is padded so each day lands on its real weekday row.
first = datetime.date.fromisoformat(days[0]["date"])
grid = [[None] * ((first.weekday() + 1) % 7)]
for d in days:
    if len(grid[-1]) == 7:
        grid.append([])
    grid[-1].append(d)
while len(grid[-1]) < 7:
    grid[-1].append(None)

n_weeks = len(grid)
W = LEFT + n_weeks * STEP + 6
H = TOP + 7 * STEP + 22
max_order = (n_weeks - 1) + 6 * 0.55

labels = []
last_month, last_label_wk = None, -10
for wk, col in enumerate(grid):
    d = next((x for x in col if x is not None), None)
    if d is None:
        continue
    month = datetime.date.fromisoformat(d["date"]).month
    if month != last_month:
        last_month = month
        if wk - last_label_wk >= 3:  # skip a label that would overlap the previous one
            last_label_wk = wk
            name = datetime.date(2000, month, 1).strftime("%b")
            labels.append(f'<text class="lbl" x="{LEFT + wk * STEP}" y="{TOP - 8}">{name}</text>')
for name, row in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
    labels.append(f'<text class="lbl" x="2" y="{TOP + row * STEP + CELL - 2}">{name}</text>')

rects = []
for wk, col in enumerate(grid):
    for row, d in enumerate(col):
        if d is None:
            continue
        lvl = max(0, min(4, int(d.get("level", 0))))
        x = LEFT + wk * STEP
        y = TOP + row * STEP
        delay = round((wk + row * 0.55) / max_order * REVEAL, 3)
        cls = "c g" if lvl else "c"
        rects.append(
            f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
            f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s"/>'
        )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:{GRAY}; font-size:13px; font-weight:600; }}
  text.total {{ fill:{INK}; font-size:15px; font-weight:700; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR + 0.15:.2f}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.1)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(2.4)}} 45%{{filter:brightness(2.4)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" fill="none"/>
{''.join(labels)}
{''.join(rects)}
<text class="total" x="{LEFT}" y="{H - 6}">{total:,} contributions in the last year</text>
</svg>'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {len(days)} days, {total:,} contributions, {len(svg) // 1024} KB")
