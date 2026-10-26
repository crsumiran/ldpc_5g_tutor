"""Draw figures/barrel8.svg: an 8-lane barrel rotator (3 columns of 2:1 muxes)
rotating A..H left by SHIFT, mux by mux.

Stage k: lane i = shift[k] ? lane (i + 2^k) mod N : lane i, as in rtl/rot_barrel.v.
The result is checked against the reference rotation before anything is drawn.

    python3 make_barrel8.py          (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_ref  # noqa: E402
from muxfig import MW, PORT, legend, mux, pill, svg_open, wire  # noqa: E402
from switchfig import LANE_Y0, PITCH, X0  # noqa: E402

N, SHIFT = 8, 5
STAGES = 3
STAGE_W = 210


def y(i):
    return LANE_Y0 + i * PITCH


values = [list("ABCDEFGH")]
for k in range(STAGES):
    sel = (SHIFT >> k) & 1
    cur = values[-1]
    values.append([cur[(i + (1 << k)) % N] if sel else cur[i] for i in range(N)])
assert values[-1] == rotl_ref(values[0], SHIFT), "figure would not match the reference"

xs = [X0 + d * STAGE_W for d in range(STAGES + 1)]
W, H = xs[-1] + 128, y(N - 1) + 88
out = svg_open(W, H, f"8-lane barrel rotator, 3 columns of 2:1 muxes, rotating A to H left by {SHIFT}")

for i in range(N):
    out.append(f'<text class="bn-lane" x="{X0 - 52}" y="{y(i)}">lane {i}</text>')
    out.append(f'<text class="bn-lane" x="{xs[-1] + 22}" y="{y(i)}">lane {i}</text>')
out.append(f'<text class="bn-head" x="{X0}" y="{LANE_Y0 - 50}">in</text>')
out.append(f'<text class="bn-head" x="{xs[-1]}" y="{LANE_Y0 - 50}">out</text>')
out.append(f'<text class="bn-sub" x="{xs[-1]}" y="{LANE_Y0 - 32}">in[(i+{SHIFT}) mod 8]</text>')

for k in range(STAGES):
    sel = (SHIFT >> k) & 1
    x0, x1 = xs[k], xs[k + 1]
    bx = x1 - 12 - 22 - MW                      # mux sits near the right of the stage
    out.append(f'<text class="bn-head" x="{(x0 + x1) / 2}" y="{LANE_Y0 - 50}">stage {k} · rotate by {1 << k}</text>')
    out.append(f'<text class="bn-sub" x="{(x0 + x1) / 2}" y="{LANE_Y0 - 32}">'
               f'every select = shift[{k}] = {sel}</text>')
    wires_off, wires_on, muxes = [], [], []
    for i in range(N):
        src = (i + (1 << k)) % N
        wrap = i + (1 << k) >= N                # the long wrap-around wires run downwards
        straight = wire(x0 + 12, y(i), bx, y(i) - PORT, on=not sel)
        long_ = wire(x0 + 12, y(src), bx, y(i) + PORT, on=bool(sel), dashed=wrap)
        (wires_on if sel else wires_off).append(long_)
        (wires_off if sel else wires_on).append(straight)
        out_w = f'<path class="bn-on" d="M{bx + MW} {y(i)} H{x1 - 12}"/>'
        muxes.append(out_w + mux(bx, y(i), str(sel), hi=bool(sel)))
    out += wires_off + wires_on + muxes

for x, vals in zip(xs, values):
    for i, v in enumerate(vals):
        out.append(pill(x, y(i), v))

out.append(legend(X0 - 52, y(N - 1) + 58,
                  f"dashed: wrap-around wires · shift = {SHIFT} = {SHIFT:03b}b"))
out.append("</svg>")
(HERE / "barrel8.svg").write_text("\n".join(out) + "\n")
print(f"wrote barrel8.svg: {' '.join(values[0])} -> {' '.join(values[-1])}")
