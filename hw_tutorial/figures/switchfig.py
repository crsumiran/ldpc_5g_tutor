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
        nxt = list(values[-1])
        for U, L, swap in st["sws"]:
            if swap:
                nxt[U], nxt[L] = nxt[L], nxt[U]
        values.append(nxt)
    return values


def y(lane):
    return LANE_Y0 + lane * PITCH


def _curve(x1, y1, x2, y2):
    mx = (x1 + x2) / 2
    return f'<path class="bn-wire" d="M{x1} {y1} C{mx} {y1} {mx} {y2} {x2} {y2}"/>'


def draw(stages, values, *, stage_w, out_sub, note, aria, groups=()):
    """stages: [{"title", "sub", "sws": [(U, L, swap), ...]}]; values from simulate().
    groups: [(first_stage, last_stage, first_lane, last_lane, label)] drawn as tinted panels;
    a group starting at lane 0 is labelled above, any other below."""
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
        out.append(f'<text class="bn-grp-t" x="{gx0 + 6}" y="{ty}">{label}</text>')

    for i in range(N):
        out.append(f'<text class="bn-lane" x="{X0 - 52}" y="{y(i)}">lane {i}</text>')
        out.append(f'<text class="bn-lane" x="{xs[-1] + 22}" y="{y(i)}">lane {i}</text>')
    out.append(f'<text class="bn-head" x="{X0}" y="{LANE_Y0 - 50}">in</text>')
    out.append(f'<text class="bn-head" x="{xs[-1]}" y="{LANE_Y0 - 50}">out</text>')
    out.append(f'<text class="bn-sub" x="{xs[-1]}" y="{LANE_Y0 - 32}">{out_sub}</text>')

    for d, st in enumerate(stages):
        x0, x1 = xs[d], xs[d + 1]
        bx = x0 + (stage_w - BOX_W) / 2
        cx = bx + BOX_W / 2
        out.append(f'<text class="bn-head" x="{cx}" y="{LANE_Y0 - 50}">{st["title"]}</text>')
        out.append(f'<text class="bn-sub" x="{cx}" y="{LANE_Y0 - 32}">{st["sub"]}</text>')
        for slot, (U, L, swap) in enumerate(st["sws"]):
            top, bot = y(2 * slot), y(2 * slot + 1)
            # lane U uses the top port, lane L the bottom one, on both sides
            out += [_curve(x0 + 12, y(U), bx, top), _curve(x0 + 12, y(L), bx, bot),
                    _curve(bx + BOX_W, top, x1 - 12, y(U)), _curve(bx + BOX_W, bot, x1 - 12, y(L))]
            cls = " x" if swap else ""
            out.append(f'<rect class="bn-box{cls}" x="{bx}" y="{top - PAD}" width="{BOX_W}" '
                       f'height="{bot - top + 2 * PAD}" rx="5"/>')
            if swap:
                out.append(f'<path class="bn-in x" d="M{bx} {top} L{bx + BOX_W} {bot} M{bx} {bot} L{bx + BOX_W} {top}"/>')
            else:
                out.append(f'<path class="bn-in" d="M{bx} {top} H{bx + BOX_W} M{bx} {bot} H{bx + BOX_W}"/>')
            out.append(f'<text class="bn-sw" x="{cx}" y="{top - PAD - 4}">{U}↔{L}</text>')

    # values on every stage boundary, drawn last so they sit on top of the wires
    for x, vals in zip(xs, values):
        for i, v in enumerate(vals):
            out.append(f'<circle class="bn-pill" cx="{x}" cy="{y(i)}" r="12"/>'
                       f'<text class="bn-val" x="{x}" y="{y(i)}">{v}</text>')

    ky = y(N - 1) + 58 + extra
    out.append(f'<rect class="bn-box" x="{X0 - 52}" y="{ky - 9}" width="22" height="18" rx="3"/>'
               f'<path class="bn-in" d="M{X0 - 52} {ky - 4} h22 M{X0 - 52} {ky + 4} h22"/>'
               f'<text class="bn-key" x="{X0 - 22}" y="{ky + 4}">bar (swap=0)</text>')
    out.append(f'<rect class="bn-box x" x="{X0 + 92}" y="{ky - 9}" width="22" height="18" rx="3"/>'
               f'<path class="bn-in x" d="M{X0 + 92} {ky - 9} l22 18 M{X0 + 92} {ky + 9} l22 -18"/>'
               f'<text class="bn-key" x="{X0 + 122}" y="{ky + 4}">cross (swap=1)</text>')
    out.append(f'<text class="bn-key" x="{X0 + 248}" y="{ky + 4}">{note}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
