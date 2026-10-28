"""Shared SVG drawing for the multistage-network figures (Banyan, Benes).

Lanes run left to right. Every stage is a column of 2x2 switches; switch
(U, L) joins lane U with lane L and puts its outputs back on lanes U and L,
exactly like the generate loops in rtl/rot_banyan.v. The colours are the page's
theme tokens with light-theme fallbacks, so the SVG works inlined in the page
(light and dark) and as a plain image on GitHub.
"""

LANE_Y0, PITCH = 96, 46
X0, BOX_W, PAD = 96, 54, 15

STYLE = """<style>
.bn .bn-bg { fill: var(--surface, #ffffff); }
.bn text { font-family: var(--font-mono, ui-monospace, Menlo, Consolas, monospace); fill: var(--ink, #15211d); }
.bn .bn-wire { fill: none; stroke: var(--muted, #56645f); stroke-width: 1.4; }
.bn .bn-box { fill: var(--surface, #ffffff); stroke: var(--ink, #15211d); stroke-width: 1.4; }
.bn .bn-box.bn-opq { stroke-dasharray: 7 5; stroke: var(--muted, #56645f); }
.bn .bn-box.x { fill: var(--accent-soft, #e1eee9); stroke: var(--hi, #b86e00); stroke-width: 2.2; }
.bn .bn-in { fill: none; stroke: var(--ink, #15211d); stroke-width: 1.6; }
.bn .bn-in.x { stroke: var(--hi, #b86e00); stroke-width: 2.2; }
.bn .bn-pill { fill: var(--surface, #ffffff); stroke: var(--accent, #0b6b57); stroke-width: 1.6; }
.bn .bn-val { font-size: 13px; font-weight: 600; text-anchor: middle; dominant-baseline: central; }
.bn .bn-lane { font-size: 12px; fill: var(--muted, #56645f); dominant-baseline: central; }
.bn .bn-head { font-size: 13px; font-weight: 600; text-anchor: middle; }
.bn .bn-sub { font-size: 11.5px; fill: var(--muted, #56645f); text-anchor: middle; }
.bn .bn-sw { font-size: 10.5px; fill: var(--muted, #56645f); text-anchor: middle; }
.bn .bn-key { font-size: 11.5px; fill: var(--muted, #56645f); }
.bn .bn-grp { fill: var(--accent-soft, #e1eee9); fill-opacity: 0.7; stroke: none; }
.bn .bn-grp-t { font-size: 11.5px; fill: var(--accent, #0b6b57); font-weight: 600; }
</style>"""


def simulate(start, stages):
    """Run values through the stages; returns the lane values before stage 0 and after each stage."""
    values = [list(start)]
    for st in stages:
        cur, nxt = values[-1], list(values[-1])
        for lanes, r in map(_norm, st["sws"]):
            m = len(lanes)
            for q in range(m):
                nxt[lanes[q]] = cur[lanes[(q + r) % m]]
        values.append(nxt)
    return values


def _norm(sw):
    """A switch is (U, L, swap) for a 2x2, or (lanes, r) for an m x m rotating
    switch whose output port q takes input port (q + r) mod m. Returns (lanes, r)."""
    if isinstance(sw[0], tuple):
        return sw
    U, L, swap = sw
    return (U, L), int(swap)


def y(lane):
    return LANE_Y0 + lane * PITCH


def _curve(x1, y1, x2, y2):
    mx = (x1 + x2) / 2
    return f'<path class="bn-wire" d="M{x1} {y1} C{mx} {y1} {mx} {y2} {x2} {y2}"/>'


def draw(stages, values, *, stage_w, out_sub, note, aria, groups=(), key=True):
    """stages: [{"title", "sub", "sws": [switch, ...], "labels"?: {slot: text},
    "inner"?: {slot: [text lines]}, "box_w"?}] (see _norm); a stage with "inner" draws each switch
    as a dashed sub-network outline holding those lines instead of its wiring;
    values from simulate().
    groups: [(first_stage, last_stage, first_lane, last_lane, label)] drawn as tinted panels;
    a group starting at lane 0 is labelled above, any other below.
    key=False leaves out the bar/cross legend (for figures without 2x2 switches)."""
    N, S = len(values[0]), len(stages)
    W = X0 + S * stage_w + 128
    extra = 22 if groups else 0                 # room for a group label under the last lane
    H_IMG = y(N - 1) + 88 + extra
    xs = [X0 + d * stage_w for d in range(S + 1)]       # stage boundaries (value pills)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H_IMG}" class="bn" '
           f'role="img" aria-label="{aria}">', STYLE,
           f'<rect class="bn-bg" x="0" y="0" width="{W}" height="{H_IMG}" rx="8"/>']

    for d0, d1, l0, l1, label in groups:
        gx0, gx1 = xs[d0] + 24, xs[d1 + 1] - 24
        top = y(l0) - 30 if l0 == 0 else y(l0) - PITCH / 2 + 2     # neighbours leave a gap at the midline
        bot = y(l1) + 26 if l1 == N - 1 else y(l1) + PITCH / 2 - 2
        out.append(f'<rect class="bn-grp" x="{gx0}" y="{top}" width="{gx1 - gx0}" '
                   f'height="{bot - top}" rx="10"/>')
        ty = top - 6 if l0 == 0 else bot + 15
        if label:
            out.append(f'<text class="bn-grp-t" x="{gx0 + 6}" y="{ty}">{label}</text>')

    for i in range(N):
        out.append(f'<text class="bn-lane" x="{X0 - 52}" y="{y(i)}">lane {i}</text>')
        out.append(f'<text class="bn-lane" x="{xs[-1] + 22}" y="{y(i)}">lane {i}</text>')
    out.append(f'<text class="bn-head" x="{X0}" y="{LANE_Y0 - 50}">in</text>')
    out.append(f'<text class="bn-head" x="{xs[-1]}" y="{LANE_Y0 - 50}">out</text>')
    out.append(f'<text class="bn-sub" x="{xs[-1]}" y="{LANE_Y0 - 32}">{out_sub}</text>')

    for d, st in enumerate(stages):
        x0, x1 = xs[d], xs[d + 1]
        bw = st.get("box_w", BOX_W)
        bx = x0 + (stage_w - bw) / 2
        cx = bx + bw / 2
        out.append(f'<text class="bn-head" x="{cx}" y="{LANE_Y0 - 50}">{st["title"]}</text>')
        out.append(f'<text class="bn-sub" x="{cx}" y="{LANE_Y0 - 32}">{st["sub"]}</text>')
        for slot, (lanes, r) in enumerate(map(_norm, st["sws"])):
            m = len(lanes)
            ports = [y(m * slot + q) for q in range(m)]
            # lane lanes[q] uses port q, on both sides
            for q, lane in enumerate(lanes):
                out += [_curve(x0 + 12, y(lane), bx, ports[q]), _curve(bx + bw, ports[q], x1 - 12, y(lane))]
            if "inner" in st:                   # a sub-network, drawn as a dashed outline with text
                out.append(f'<rect class="bn-box bn-opq" x="{bx}" y="{ports[0] - PAD}" width="{bw}" '
                           f'height="{ports[-1] - ports[0] + 2 * PAD}" rx="8"/>')
                lines = st["inner"][slot]
                ymid = (ports[0] + ports[-1]) / 2 - (len(lines) - 1) * 9
                out += [f'<text class="bn-sub" x="{cx}" y="{ymid + 18 * i + 4}">{t}</text>'
                        for i, t in enumerate(lines)]
                continue
            cls = " x" if r else ""
            out.append(f'<rect class="bn-box{cls}" x="{bx}" y="{ports[0] - PAD}" width="{BOX_W}" '
                       f'height="{ports[-1] - ports[0] + 2 * PAD}" rx="5"/>')
            if m == 2 and r:
                out.append(f'<path class="bn-in x" d="M{bx} {ports[0]} L{bx + BOX_W} {ports[1]} '
                           f'M{bx} {ports[1]} L{bx + BOX_W} {ports[0]}"/>')
            elif m == 2:
                out.append(f'<path class="bn-in" d="M{bx} {ports[0]} H{bx + BOX_W} M{bx} {ports[1]} H{bx + BOX_W}"/>')
            else:                               # output port q <- input port (q + r) mod m
                out.append(f'<path class="bn-in{cls}" d="' + " ".join(
                    f"M{bx} {ports[(q + r) % m]} L{bx + BOX_W} {ports[q]}" for q in range(m)) + '"/>')
            label = f"{lanes[0]}↔{lanes[1]}" if m == 2 else "·".join(map(str, lanes)) + f" r={r}"
            label = st.get("labels", {}).get(slot, label)
            out.append(f'<text class="bn-sw" x="{cx}" y="{ports[0] - PAD - 4}">{label}</text>')

    # values on every stage boundary, drawn last so they sit on top of the wires
    for x, vals in zip(xs, values):
        for i, v in enumerate(vals):
            out.append(f'<circle class="bn-pill" cx="{x}" cy="{y(i)}" r="12"/>'
                       f'<text class="bn-val" x="{x}" y="{y(i)}">{v}</text>')

    ky = y(N - 1) + 58 + extra
    if not key:
        out.append(f'<text class="bn-key" x="{X0 - 52}" y="{ky + 4}">{note}</text>')
        out.append("</svg>")
        return "\n".join(out) + "\n"
    out.append(f'<rect class="bn-box" x="{X0 - 52}" y="{ky - 9}" width="22" height="18" rx="3"/>'
               f'<path class="bn-in" d="M{X0 - 52} {ky - 4} h22 M{X0 - 52} {ky + 4} h22"/>'
               f'<text class="bn-key" x="{X0 - 22}" y="{ky + 4}">bar (swap=0)</text>')
    out.append(f'<rect class="bn-box x" x="{X0 + 92}" y="{ky - 9}" width="22" height="18" rx="3"/>'
               f'<path class="bn-in x" d="M{X0 + 92} {ky - 9} l22 18 M{X0 + 92} {ky + 9} l22 -18"/>'
               f'<text class="bn-key" x="{X0 + 122}" y="{ky + 4}">cross (swap=1)</text>')
    out.append(f'<text class="bn-key" x="{X0 + 248}" y="{ky + 4}">{note}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
