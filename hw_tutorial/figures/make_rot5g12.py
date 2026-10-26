"""Draw figures/rot5g12.svg: the 5G rotator structure (rtl/rot_5g.v) at N = 12:
two full-size cyclic rotators (IBNs) plus a merge column rotate a Z-element
vector, Z < N, left by SHIFT.

    A = rotl_N(din, s)                 correct for lanes i <  Z - s
    B = rotl_N(din, (N - Z + s) mod N) correct for lanes i >= Z - s
    dout[i] = i < Z - s ? A[i] : B[i]  for i < Z

Each rotator is drawn as a box showing its lane mapping (its insides are the
IBN figure). Checked against rotl_bypass(rot=rotl_ibn) and the reference.

    python3 make_rot5g12.py          (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_bypass, rotl_ibn, rotl_ref  # noqa: E402
from muxfig import MW, PORT, legend, mux, pill, svg_open, wire  # noqa: E402
from switchfig import X0  # noqa: E402

N, Z, SHIFT = 12, 10, 7
S2 = (N - Z + SHIFT) % N
R = Z - SHIFT                                   # merge threshold
P, GAP, Y0 = 34, 84, 124
BOX_X0, BOX_X1 = X0 + 40, X0 + 250              # rotator box
XA = BOX_X1 + 40                                # rotator output pills
XM = XA + 200                                   # merge muxes
XO = XM + MW + 44                               # dout pills

din = [chr(ord("A") + i) for i in range(Z)] + ["0"] * (N - Z)
rotA = rotl_ibn(din, SHIFT)
rotB = rotl_ibn(din, S2)
dout = [rotA[i] if i < R else rotB[i] for i in range(Z)]
assert dout == rotl_bypass(din, SHIFT, Z, rot=rotl_ibn)[:Z] == rotl_ref(din[:Z], SHIFT), "figure would not match"


def y_a(i):
    return Y0 + i * P


def y_b(i):
    return Y0 + N * P + GAP + i * P


def y_m(i):
    return (y_a(i) + y_b(i)) / 2


W, H = XO + 92, y_b(N - 1) + 104
out = svg_open(W, H, f"5G rotator structure at N = {N}: two {N}-lane IBN rotators and a merge column "
                     f"rotate a {Z}-element vector left by {SHIFT}")
out.append('<style>.bn .bn-rot { fill: var(--surface, #ffffff); stroke: var(--ink, #15211d); stroke-width: 1.4; }</style>')

for x, t in ((X0, "din"), ((BOX_X0 + BOX_X1) / 2, "full-size rotators"), (XA, "A / B"), (XM + MW / 2, "merge"),
             (XO, "dout")):
    out.append(f'<text class="bn-head" x="{x}" y="{Y0 - 66}">{t}</text>')
out.append(f'<text class="bn-panel" x="{X0 - 52}" y="{y_a(0) - 34}">IBN-{N} #1 · rotl by s = {SHIFT} → A</text>')
out.append(f'<text class="bn-panel" x="{X0 - 52}" y="{y_b(0) - 34}">IBN-{N} #2 · rotl by s2 = (N − Z + s) mod N = '
           f'({N} − {Z} + {SHIFT}) mod {N} = {S2} → B</text>')


def panel(shift, vals, yf, used):
    out.append(f'<rect class="bn-rot" x="{BOX_X0}" y="{yf(0) - 18}" width="{BOX_X1 - BOX_X0}" '
               f'height="{yf(N - 1) - yf(0) + 36}" rx="8"/>')
    offs, ons = [], []
    for i in range(N):
        out.append(f'<text class="bn-lane" x="{X0 - 52}" y="{yf(i)}">lane {i}</text>')
        src = (i + shift) % N
        w_ = wire(BOX_X0 + 6, yf(src), BOX_X1 - 6, yf(i), on=used(i), dashed=i + shift >= N)
        (ons if used(i) else offs).append(w_)
        offs.append(f'<path class="bn-off" d="M{X0 + 12} {yf(i)} H{BOX_X0}"/>'
                    f'<path class="bn-off" d="M{BOX_X1} {yf(i)} H{XA - 12}"/>')
    out.extend(offs + ons)
    for i in range(N):
        out.append(pill(X0, yf(i), din[i]))
        out.append(pill(XA, yf(i), vals[i]))


panel(SHIFT, rotA, y_a, lambda i: i < R)
panel(S2, rotB, y_b, lambda i: R <= i < Z)

offs, ons, muxes = [], [], []
for i in range(N):
    valid = i < Z
    sel = 0 if i < R else 1
    for yy, port, on in ((y_a(i), -PORT, valid and sel == 0), (y_b(i), PORT, valid and sel == 1)):
        (ons if on else offs).append(wire(XA + 12, yy, XM, y_m(i) + port, on=on))
    o = "bn-on" if valid else "bn-off"
    muxes.append(f'<path class="{o}" d="M{XM + MW} {y_m(i)} H{XO - 12}"/>'
                 + mux(XM, y_m(i), str(sel) if valid else "–", hi=valid and sel == 1))
    muxes.append(pill(XO, y_m(i), dout[i] if valid else "·"))
    muxes.append(f'<text class="bn-lane" x="{XO + 20}" y="{y_m(i)}">lane {i}</text>')
out.extend(offs + ons + muxes)
mtop = y_m(0) - 50
out.append(f'<text class="bn-sub" x="{XM + MW / 2}" y="{mtop - 16}">select = (i ≥ Z − s), Z − s = {R}</text>')
out.append(f'<text class="bn-sub" x="{XM + MW / 2}" y="{mtop}">lanes 0–{R - 1}: A · {R}–{Z - 1}: B</text>')
out.append(f'<text class="bn-sub" x="{XM + MW / 2}" y="{y_m(N - 1) + 38}">lanes {Z}–{N - 1}: unused (i ≥ Z)</text>')

out.append(legend(X0 - 52, y_b(N - 1) + 52, f"dashed: wraps at lane N · N = {N}, Z = {Z}, s = {SHIFT}", note_below=True))
out.append("</svg>")
(HERE / "rot5g12.svg").write_text("\n".join(out) + "\n")
print(f"wrote rot5g12.svg: {' '.join(din)} -> {' '.join(dout)}  (s2 = {S2})")
