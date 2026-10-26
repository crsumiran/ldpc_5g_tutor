"""Draw figures/qsn8.svg: the QSN variable-size rotator on 8 lanes, rotating a
Z-element vector left by SHIFT with two non-circular shifters and a merge column.

    left  = din << s          (stage k: lane i = s[k]     ? lane i + 2^k, or 0 : lane i)
    right = din >> (Z - s)    (stage k: lane i = (Z-s)[k] ? lane i - 2^k, or 0 : lane i)
    dout[i] = i < Z - s ? left[i] : right[i]      for i < Z, else 0

as in rtl/rot_qsn.v. The result is checked against rotl_qsn and the reference
rotation of the first Z lanes before anything is drawn.

    python3 make_qsn8.py             (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_qsn, rotl_ref  # noqa: E402
from muxfig import MW, PORT, legend, mux, pill, svg_open, wire, zero_in  # noqa: E402
from switchfig import X0  # noqa: E402

N, Z, SHIFT = 8, 5, 2
R = Z - SHIFT                                   # right-shift amount, one subtractor in hardware
STAGES = 3
STAGE_W, P, GAP, Y0 = 150, 40, 84, 124
MERGE_W = 250


def y_left(i):
    return Y0 + i * P


def y_right(i):
    return Y0 + N * P + GAP + i * P


def y_merge(i):
    return (y_left(i) + y_right(i)) / 2


din = list("ABCDE") + ["0"] * (N - Z)


def shifter(amount, direction):
    """Non-circular log shifter. Returns lane values per stage and the source of each mux's input 1."""
    vals, srcs = [din], []
    for k in range(STAGES):
        sel = (amount >> k) & 1
        src = [i + direction * (1 << k) for i in range(N)]
        src = [j if 0 <= j < N else None for j in src]          # None: constant 0 input
        cur = vals[-1]
        vals.append([(cur[src[i]] if src[i] is not None else "0") if sel else cur[i] for i in range(N)])
        srcs.append((sel, src))
    return vals, srcs


left, left_src = shifter(SHIFT, +1)
right, right_src = shifter(R, -1)
dout = [left[-1][i] if i < R else right[-1][i] for i in range(Z)] + ["0"] * (N - Z)
assert dout[:Z] == rotl_qsn(din, SHIFT, Z)[:Z] == rotl_ref(din[:Z], SHIFT), "figure would not match"

xs = [X0 + d * STAGE_W for d in range(STAGES + 1)]
xm = xs[-1] + MERGE_W - 70                      # merge muxes
xo = xm + MW + 44                               # output pills
W, H = xo + 92, y_right(N - 1) + 84
out = svg_open(W, H, f"8-lane QSN rotator: left shifter, right shifter and merge, rotating a {Z}-element "
                     f"vector left by {SHIFT}")

for k in range(STAGES):
    out.append(f'<text class="bn-head" x="{(xs[k] + xs[k + 1]) / 2}" y="{Y0 - 66}">stage {k} · by {1 << k}</text>')
out.append(f'<text class="bn-head" x="{X0}" y="{Y0 - 66}">din</text>')
out.append(f'<text class="bn-head" x="{xm + MW / 2}" y="{Y0 - 66}">merge</text>')
out.append(f'<text class="bn-head" x="{xo}" y="{Y0 - 66}">dout</text>')
out.append(f'<text class="bn-panel" x="{X0 - 52}" y="{y_left(0) - 34}">left shifter: din &lt;&lt; s · '
           f's = {SHIFT} = {SHIFT:03b}b · mux select = s[k]</text>')
out.append(f'<text class="bn-panel" x="{X0 - 52}" y="{y_right(0) - 34}">right shifter: din &gt;&gt; (Z − s) · '
           f'Z − s = {R} = {R:03b}b · mux select = (Z − s)[k]</text>')


def panel(vals, srcs, yf):
    offs, ons, muxes = [], [], []
    for i in range(N):
        out.append(f'<text class="bn-lane" x="{X0 - 52}" y="{yf(i)}">lane {i}</text>')
    for k, (sel, src) in enumerate(srcs):
        x0, x1 = xs[k], xs[k + 1]
        bx = x1 - 12 - 18 - MW
        for i in range(N):
            straight = wire(x0 + 12, yf(i), bx, yf(i) - PORT, on=not sel)
            (offs if sel else ons).append(straight)
            if src[i] is None:
                (ons if sel else offs).append(zero_in(bx, yf(i) + PORT).replace(
                    'class="bn-off"', f'class="{"bn-on" if sel else "bn-off"}"'))
            else:
                (ons if sel else offs).append(wire(x0 + 12, yf(src[i]), bx, yf(i) + PORT, on=bool(sel)))
            muxes.append(f'<path class="bn-on" d="M{bx + MW} {yf(i)} H{x1 - 12}"/>' + mux(bx, yf(i), str(sel), hi=bool(sel)))
    out.extend(offs + ons + muxes)


panel(left, left_src, y_left)
panel(right, right_src, y_right)

# merge column: input 0 from the left shifter, input 1 from the right shifter
offs, ons, muxes = [], [], []
for i in range(N):
    valid = i < Z
    sel = 0 if i < R else 1
    a = wire(xs[-1] + 12, y_left(i), xm, y_merge(i) - PORT, on=valid and sel == 0)
    b = wire(xs[-1] + 12, y_right(i), xm, y_merge(i) + PORT, on=valid and sel == 1)
    for w_, on in ((a, valid and sel == 0), (b, valid and sel == 1)):
        (ons if on else offs).append(w_)
    o = "bn-on" if valid else "bn-off"
    muxes.append(f'<path class="{o}" d="M{xm + MW} {y_merge(i)} H{xo - 12}"/>'
                 + mux(xm, y_merge(i), str(sel) if valid else "–", hi=valid and sel == 1))
    muxes.append(f'<text class="bn-lane" x="{xo + 20}" y="{y_merge(i)}">lane {i}</text>')
out.extend(offs + ons + muxes)
mtop = y_merge(0) - 52
out.append(f'<text class="bn-sub" x="{xm + MW / 2}" y="{mtop - 16}">select = (i ≥ Z − s)</text>')
out.append(f'<text class="bn-sub" x="{xm + MW / 2}" y="{mtop}">lanes 0–{R - 1}: left · {R}–{Z - 1}: right</text>')
out.append(f'<text class="bn-sub" x="{xm + MW / 2}" y="{y_merge(N - 1) + 40}">lanes {Z}–{N - 1}: unused (i ≥ Z)</text>')

for vals, yf in ((left, y_left), (right, y_right)):
    for x, col in zip(xs, vals):
        for i, v in enumerate(col):
            out.append(pill(x, yf(i), v))
for i, v in enumerate(dout):
    out.append(pill(xo, y_merge(i), v if i < Z else "·"))

out.append(legend(X0 - 52, y_right(N - 1) + 54, f"N = {N}, Z = {Z}, s = {SHIFT}"))
out.append("</svg>")
(HERE / "qsn8.svg").write_text("\n".join(out) + "\n")
print(f"wrote qsn8.svg: {' '.join(din)} -> {' '.join(dout[:Z])}")
