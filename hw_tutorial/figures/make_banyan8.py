"""Draw figures/banyan8.svg: an 8-lane Banyan rotator (3 stages of 2x2 switches)
carrying A..H through a left rotation by SHIFT.

The switch settings come from the same rule as rtl/rot_banyan.v, and the
result is checked against the reference rotation before anything is drawn.

    python3 make_banyan8.py          (run from this folder)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "model"))
from rotators import rotl_ref  # noqa: E402

N, SHIFT = 8, 3
n = N.bit_length() - 1

# ---- simulate the network lane by lane, exactly like rot_banyan.v
values = [list("ABCDEFGH")]
stages = []                       # per stage: (H, a, b, [(U, L, swap), ...])
for d in range(n):
    B = N >> d
    H = B // 2
    a = (SHIFT >> (n - 1 - d)) & 1
    b = SHIFT & (H - 1)
    cur, nxt, sws = values[-1], list(values[-1]), []
    for j in range(N // B):
        for k in range(H):
            U, L = j * B + k, j * B + k + H
            swap = a ^ (k < b)
            nxt[U], nxt[L] = (cur[L], cur[U]) if swap else (cur[U], cur[L])
            sws.append((U, L, swap))
    stages.append((H, a, b, sws))
    values.append(nxt)
assert values[-1] == rotl_ref(values[0], SHIFT), "figure would not match the reference"

# ---- geometry
LANE_Y0, PITCH = 96, 46
STAGE_X0, STAGE_W = 96, 200
FAN, BOX_W, PAD = 62, 54, 15
W = STAGE_X0 + n * STAGE_W + 128
H_IMG = LANE_Y0 + (N - 1) * PITCH + 88


def y(lane):
    return LANE_Y0 + lane * PITCH


def curve(x1, y1, x2, y2, cls):
    mx = (x1 + x2) / 2
    return f'<path class="{cls}" d="M{x1} {y1} C{mx} {y1} {mx} {y2} {x2} {y2}"/>'


def pill(x, yy, v):
    return (f'<circle class="bn-pill" cx="{x}" cy="{yy}" r="12"/>'
            f'<text class="bn-val" x="{x}" y="{yy}">{v}</text>')


out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H_IMG}" class="bn" '
       f'role="img" aria-label="8-lane Banyan network, 3 stages of four 2x2 switches, rotating A to H left by {SHIFT}">',
       """<style>
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
</style>""",
       f'<rect class="bn-bg" x="0" y="0" width="{W}" height="{H_IMG}" rx="8"/>']

# lane numbers, input and output captions
for i in range(N):
    out.append(f'<text class="bn-lane" x="{STAGE_X0 - 52}" y="{y(i)}">lane {i}</text>')
    out.append(f'<text class="bn-lane" x="{STAGE_X0 + n * STAGE_W + 22}" y="{y(i)}">lane {i}</text>')
out.append(f'<text class="bn-head" x="{STAGE_X0}" y="{LANE_Y0 - 50}">in</text>')
out.append(f'<text class="bn-head" x="{STAGE_X0 + n * STAGE_W}" y="{LANE_Y0 - 50}">out</text>')
out.append(f'<text class="bn-sub" x="{STAGE_X0 + n * STAGE_W}" y="{LANE_Y0 - 32}">in[(i+{SHIFT}) mod 8]</text>')

for d, (H, a, b, sws) in enumerate(stages):
    x0 = STAGE_X0 + d * STAGE_W
    bx = x0 + (STAGE_W - BOX_W) / 2
    x1 = x0 + STAGE_W
    cx = bx + BOX_W / 2
    out.append(f'<text class="bn-head" x="{cx}" y="{LANE_Y0 - 50}">stage {d} · span {H}</text>')
    thermo = "all cross" if (a and b == 0) else ("all bar" if (not a and b == 0) else
              f"k&lt;{b} {'bar' if a else 'cross'}, rest {'cross' if a else 'bar'}")
    out.append(f'<text class="bn-sub" x="{cx}" y="{LANE_Y0 - 32}">a={a} b={b} → {thermo}</text>')
    for slot, (U, L, swap) in enumerate(sws):
        top, bot = y(2 * slot), y(2 * slot + 1)
        cls = " x" if swap else ""
        # wires into and out of the switch: lane U uses the top port, lane L the bottom
        out.append(curve(x0 + 12, y(U), bx, top, "bn-wire"))
        out.append(curve(x0 + 12, y(L), bx, bot, "bn-wire"))
        out.append(curve(bx + BOX_W, top, x1 - 12, y(U), "bn-wire"))
        out.append(curve(bx + BOX_W, bot, x1 - 12, y(L), "bn-wire"))
        out.append(f'<rect class="bn-box{cls}" x="{bx}" y="{top - PAD}" width="{BOX_W}" '
                   f'height="{bot - top + 2 * PAD}" rx="5"/>')
        if swap:
            out.append(f'<path class="bn-in x" d="M{bx} {top} L{bx + BOX_W} {bot} M{bx} {bot} L{bx + BOX_W} {top}"/>')
        else:
            out.append(f'<path class="bn-in" d="M{bx} {top} H{bx + BOX_W} M{bx} {bot} H{bx + BOX_W}"/>')
        out.append(f'<text class="bn-sw" x="{cx}" y="{top - PAD - 4}">{U}↔{L}</text>')

# values on every stage boundary, drawn last so they sit on top of the wires
for d, vals in enumerate(values):
    x = STAGE_X0 + d * STAGE_W
    for i, v in enumerate(vals):
        out.append(pill(x, y(i), v))

ky = y(N - 1) + 58
out.append(f'<rect class="bn-box" x="{STAGE_X0 - 52}" y="{ky - 9}" width="22" height="18" rx="3"/>'
           f'<path class="bn-in" d="M{STAGE_X0 - 52} {ky - 4} h22 M{STAGE_X0 - 52} {ky + 4} h22"/>'
           f'<text class="bn-key" x="{STAGE_X0 - 22}" y="{ky + 4}">bar (swap=0)</text>')
out.append(f'<rect class="bn-box x" x="{STAGE_X0 + 92}" y="{ky - 9}" width="22" height="18" rx="3"/>'
           f'<path class="bn-in x" d="M{STAGE_X0 + 92} {ky - 9} l22 18 M{STAGE_X0 + 92} {ky + 9} l22 -18"/>'
           f'<text class="bn-key" x="{STAGE_X0 + 122}" y="{ky + 4}">cross (swap=1)</text>')
out.append(f'<text class="bn-key" x="{STAGE_X0 + 248}" y="{ky + 4}">'
           f'shift = {SHIFT} = {SHIFT:03b}b · a = one shift bit, b = shift mod span · swap[k] = a XOR (k &lt; b)</text>')
out.append("</svg>")

dst = Path(__file__).with_name("banyan8.svg")
dst.write_text("\n".join(out) + "\n")
print(f"wrote {dst.name}: {' '.join(values[0])} -> {' '.join(values[-1])}")
