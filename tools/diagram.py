#!/usr/bin/env python3
"""Generate the home-page edge diagram (two inline SVG variants: wide and compact).

Writes src/partials/edge-diagram.html. Python 3 standard library only.
The SVG uses presentation attributes and classes only (no inline style),
so it works under the site's Content Security Policy.
"""
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "partials" / "edge-diagram.html"

random.seed(7)  # deterministic output


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def wide():
    w, h = 1100, 340
    band_x, band_w = 500, 44
    dests = [(92, "Banks and credit unions"), (180, "Healthcare software vendors"), (268, "Health systems and hospitals")]
    dest_x, dest_w, dest_h = 846, 254, 52
    n = 17
    blocked = {1, 4, 7, 10, 14}
    starts = [40 + i * (280 / (n - 1)) + random.uniform(-6, 6) for i in range(n)]
    ends = [70 + i * (200 / (n - 1)) for i in range(n)]
    paths, ticks = [], []
    for i in range(n):
        y0, ye = starts[i], ends[i]
        c1 = 220 + random.uniform(-30, 30)
        c2 = 330 + random.uniform(-30, 30)
        if i in blocked:
            paths.append(f'<path class="blocked" d="M0 {f(y0)} C{f(c1)} {f(y0)} {f(c2)} {f(ye)} {band_x} {f(ye)}" pathLength="1"/>')
            ticks.append(f'<path class="tick" d="M{band_x - 2} {f(ye - 7)} L{band_x - 2} {f(ye + 7)}"/>')
        else:
            passing = [k for k in range(n) if k not in blocked]
            dy = dests[passing.index(i) * 3 // len(passing)][0]
            x1 = band_x + band_w
            paths.append(
                f'<path class="pass d{i % 6}" d="M0 {f(y0)} C{f(c1)} {f(y0)} {f(c2)} {f(ye)} {band_x} {f(ye)} '
                f'L{x1} {f(ye)} C{f(x1 + 150)} {f(ye)} {f(dest_x - 140)} {f(dy)} {dest_x} {f(dy)}" pathLength="1"/>'
            )
    boxes = []
    for y, label in dests:
        boxes.append(
            f'<rect class="dest" x="{dest_x}" y="{f(y - dest_h / 2)}" width="{dest_w}" height="{dest_h}" rx="3"/>'
            f'<text class="dest-label" x="{dest_x + 18}" y="{f(y + 6)}">{label}</text>'
        )
    return f"""<svg class="edge-diagram edge-wide" viewBox="0 0 {w} {h}" role="img" aria-labelledby="ed-title ed-desc">
  <title id="ed-title">Traffic passing through the edge layer</title>
  <desc id="ed-desc">Lines of internet traffic converge on a vertical band labelled Edge. Some lines, representing automated attacks, stop at the edge. The rest pass through to banks and credit unions, healthcare software vendors, and health systems and hospitals.</desc>
  <text class="zone-label" x="0" y="18">Internet</text>
  <text class="zone-label" x="{band_x + band_w / 2}" y="18" text-anchor="middle">Edge</text>
  <rect class="band" x="{band_x}" y="30" width="{band_w}" height="{h - 40}" rx="2"/>
  <g class="flow">
    {chr(10).join('    ' + p for p in paths).strip()}
  </g>
  <g class="ticks">
    {chr(10).join('    ' + t for t in ticks).strip()}
  </g>
  {''.join(boxes)}
</svg>"""


def compact():
    w, h = 360, 470
    band_y, band_h = 196, 30
    dests = [(60, ["Banks and", "credit unions"]), (180, ["Healthcare", "software vendors"]), (300, ["Health systems", "and hospitals"])]
    dest_y, dest_w, dest_h = 404, 112, 60
    n = 13
    blocked = {1, 5, 8, 11}
    starts = [12 + i * (336 / (n - 1)) + random.uniform(-4, 4) for i in range(n)]
    ends = [70 + i * (220 / (n - 1)) for i in range(n)]
    paths, ticks = [], []
    for i in range(n):
        x0, xe = starts[i], ends[i]
        c1 = 80 + random.uniform(-15, 15)
        c2 = 130 + random.uniform(-15, 15)
        if i in blocked:
            paths.append(f'<path class="blocked" d="M{f(x0)} 30 C{f(x0)} {f(c1)} {f(xe)} {f(c2)} {f(xe)} {band_y}" pathLength="1"/>')
            ticks.append(f'<path class="tick" d="M{f(xe - 6)} {band_y - 2} L{f(xe + 6)} {band_y - 2}"/>')
        else:
            passing = [k for k in range(n) if k not in blocked]
            dx = dests[passing.index(i) * 3 // len(passing)][0]
            y1 = band_y + band_h
            paths.append(
                f'<path class="pass d{i % 6}" d="M{f(x0)} 30 C{f(x0)} {f(c1)} {f(xe)} {f(c2)} {f(xe)} {band_y} '
                f'L{f(xe)} {y1} C{f(xe)} {y1 + 80} {dx} {dest_y - 90} {dx} {dest_y - dest_h / 2}" pathLength="1"/>'
            )
    boxes = []
    for x, lines in dests:
        boxes.append(
            f'<rect class="dest" x="{f(x - dest_w / 2)}" y="{f(dest_y - dest_h / 2)}" width="{dest_w}" height="{dest_h}" rx="3"/>'
            f'<text class="dest-label small" x="{x}" y="{f(dest_y - 4)}" text-anchor="middle">'
            f'<tspan x="{x}">{lines[0]}</tspan><tspan x="{x}" dy="17">{lines[1]}</tspan></text>'
        )
    return f"""<svg class="edge-diagram edge-compact" viewBox="0 0 {w} {h}" role="img" aria-labelledby="ec-title ec-desc">
  <title id="ec-title">Traffic passing through the edge layer</title>
  <desc id="ec-desc">Lines of internet traffic converge on a band labelled Edge. Some lines, representing automated attacks, stop at the edge. The rest pass through to banks and credit unions, healthcare software vendors, and health systems and hospitals.</desc>
  <text class="zone-label" x="0" y="16">Internet</text>
  <text class="zone-label" x="0" y="{band_y - 10}">Edge</text>
  <rect class="band" x="0" y="{band_y}" width="{w}" height="{band_h}" rx="2"/>
  <g class="flow">
    {chr(10).join('    ' + p for p in paths).strip()}
  </g>
  <g class="ticks">
    {chr(10).join('    ' + t for t in ticks).strip()}
  </g>
  {''.join(boxes)}
</svg>"""


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(wide() + "\n" + compact() + "\n", encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
