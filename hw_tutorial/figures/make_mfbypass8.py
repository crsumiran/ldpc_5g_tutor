"""Draw figures/mfbypass8.svg: multi-frame mode and the bypass/merge working
together. An 8-lane network carries two frames of Z = 3 elements, each in its
own 4-lane sub-network, rotated by its own shift.

Both rotators are multi-frame Banyans (stage 0 forced to bar). Per frame j,
with local lane l = i mod 4:

    A = rotl_4(frame, s_j)                    correct for l <  Z - s_j
    B = rotl_4(frame, (4 - Z + s_j) mod 4)    correct for l >= Z - s_j
    dout[i] = l < Z - s_j ? A[i] : B[i]       for l < Z

Checked against rotl_bypass per frame and the reference rotation.

    python3 make_mfbypass8.py        (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_banyan, rotl_banyan_multiframe, rotl_bypass, rotl_ref  # noqa: E402
from muxfig import MW, PORT, legend, mux, pill, svg_open, wire  # noqa: E402
from switchfig import X0  # noqa: E402

N, FS, Z = 8, 4, 3                              # lanes, frame (sub-network) size, vector length
SHIFTS = [1, 2]
S2 = [(FS - Z + s) % FS for s in SHIFTS]
P, GAP, Y0 = 34, 96, 132
BOX_X0, BOX_X1 = X0 + 40, X0 + 250
XA = BOX_X1 + 40
XM = XA + 200
XO = XM + MW + 44

frames = [["A", "B", "C"], ["D", "E", "F"]]
din = sum((f + ["0"] * (FS - Z) for f in frames), [])
rotA = rotl_banyan_multiframe(din, SHIFTS)
rotB = rotl_banyan_multiframe(din, S2)


def frame_of(i):
    return i // FS, i % FS


def sel(i):
    j, l = frame_of(i)
    return 0 if l < Z - SHIFTS[j] else 1


dout = [(rotA[i] if sel(i) == 0 else rotB[i]) if frame_of(i)[1] < Z else "·" for i in range(N)]
for j, s in enumerate(SHIFTS):
    got = dout[j * FS:j * FS + Z]
    assert got == rotl_ref(frames[j], s) == rotl_bypass(din[j * FS:(j + 1) * FS], s, Z, rot=rotl_banyan)[:Z], \
        "figure would not match"


def y_a(i):
    return Y0 + i * P + (i >= FS) * 14


def y_b(i):
    return y_a(N - 1) + GAP + y_a(i) - Y0 + P


def y_m(i):
    return (y_a(i) + y_b(i)) / 2


W, H = XO + 92, y_b(N - 1) + 104
out = svg_open(W, H, f"Multi-frame bypass: an {N}-lane network carries two {Z}-element frames in {FS}-lane "
                     f"sub-networks, rotated left by {SHIFTS[0]} and {SHIFTS[1]}")
out.append('<style>.bn .bn-rot { fill: var(--surface, #ffffff); stroke: var(--ink, #15211d); stroke-width: 1.4; }'
           '.bn .bn-fb { stroke: var(--hi, #b86e00); stroke-width: 1.4; stroke-dasharray: 5 4; }</style>')

for x, t in ((X0, "din"), ((BOX_X0 + BOX_X1) / 2, "multi-frame rotators"), (XA, "A / B"), (XM + MW / 2, "merge"),
             (XO, "dout")):
    out.append(f'<text class="bn-head" x="{x}" y="{Y0 - 70}">{t}</text>')
out.append(f'<text class="bn-panel" x="{X0 - 52}" y="{y_a(0) - 36}">rotator #1 · frame 0 rotl {SHIFTS[0]}, '
           f'frame 1 rotl {SHIFTS[1]} → A</text>')
out.append(f'<text class="bn-panel" x="{X0 - 52}" y="{y_b(0) - 36}">rotator #2 · per frame (4 − Z + s) mod 4 '
           f'= {S2[0]}, {S2[1]} → B</text>')


def panel(shifts, vals, yf, used):
    out.append(f'<rect class="bn-rot" x="{BOX_X0}" y="{yf(0) - 18}" width="{BOX_X1 - BOX_X0}" '
               f'height="{yf(N - 1) - yf(0) + 36}" rx="8"/>')
    yb = (yf(FS - 1) + yf(FS)) / 2
    out.append(f'<path class="bn-fb" d="M{BOX_X0} {yb} H{BOX_X1}"/>')
    offs, ons = [], []
    for i in range(N):
        j, l = frame_of(i)
        out.append(f'<text class="bn-lane" x="{X0 - 52}" y="{yf(i)}">lane {i}</text>')
        src = j * FS + (l + shifts[j]) % FS
        w_ = wire(BOX_X0 + 6, yf(src), BOX_X1 - 6, yf(i), on=used(i), dashed=l + shifts[j] >= FS)
        (ons if used(i) else offs).append(w_)
        offs.append(f'<path class="bn-off" d="M{X0 + 12} {yf(i)} H{BOX_X0}"/>'
                    f'<path class="bn-off" d="M{BOX_X1} {yf(i)} H{XA - 12}"/>')
    out.extend(offs + ons)
    for i in range(N):
        out.append(pill(X0, yf(i), din[i]))
        out.append(pill(XA, yf(i), vals[i]))


panel(SHIFTS, rotA, y_a, lambda i: frame_of(i)[1] < Z and sel(i) == 0)
panel(S2, rotB, y_b, lambda i: frame_of(i)[1] < Z and sel(i) == 1)

offs, ons, muxes = [], [], []
for i in range(N):
    valid = frame_of(i)[1] < Z
    s_ = sel(i)
    for yy, port, on in ((y_a(i), -PORT, valid and s_ == 0), (y_b(i), PORT, valid and s_ == 1)):
        (ons if on else offs).append(wire(XA + 12, yy, XM, y_m(i) + port, on=on))
    o = "bn-on" if valid else "bn-off"
    muxes.append(f'<path class="{o}" d="M{XM + MW} {y_m(i)} H{XO - 12}"/>'
                 + mux(XM, y_m(i), str(s_) if valid else "–", hi=valid and s_ == 1))
    muxes.append(pill(XO, y_m(i), dout[i]))
    muxes.append(f'<text class="bn-lane" x="{XO + 20}" y="{y_m(i)}">lane {i}</text>')
out.extend(offs + ons + muxes)
mtop = Y0 - 26
out.append(f'<text class="bn-sub" x="{XM + MW / 2}" y="{mtop - 16}">select = (l ≥ Z − s_j), l = lane in frame</text>')
out.append(f'<text class="bn-sub" x="{XM + MW / 2}" y="{mtop}">frame 0: Z − s = {Z - SHIFTS[0]} · '
           f'frame 1: Z − s = {Z - SHIFTS[1]}</text>')
out.append(f'<text class="bn-sub" x="{XM + MW / 2}" y="{y_m(N - 1) + 40}">lanes 3 and 7: unused (l ≥ Z)</text>')

out.append(legend(X0 - 52, y_b(N - 1) + 52, f"dashed: wraps inside its frame · orange dashed line: frame boundary, "
                                             f"stage 0 forced bar · Z = {Z}", note_below=True))
out.append("</svg>")
(HERE / "mfbypass8.svg").write_text("\n".join(out) + "\n")
print(f"wrote mfbypass8.svg: {' '.join(din)} -> {' '.join(dout)}  (A = {''.join(rotA)}, B = {''.join(rotB)}, s2 = {S2})")
