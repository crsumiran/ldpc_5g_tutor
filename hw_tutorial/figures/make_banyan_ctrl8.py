"""Draw figures/banyan_ctrl8.svg: the control generator of an 8-lane Banyan
(rtl/rot_banyan.v) for shift = 5. Per stage d:

    a_d = shift[n-1-d]                one wire
    b_d = shift & (H-1)               low bits, no arithmetic
    t[k] = (k < b_d)                  thermometer, k = 0..H-1
    swap[k] = a_d XOR t[k]            drives switch k of EVERY block

The swaps are fed through the switch network and checked against the
reference rotation before drawing.

    python3 make_banyan_ctrl8.py     (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_ref  # noqa: E402
from muxfig import pill, svg_open  # noqa: E402
from switchfig import simulate  # noqa: E402

N, SHIFT = 8, 5
n = N.bit_length() - 1
LM, CW, KP = 120, 280, 56                       # left margin, column width, k pitch
Y_REG, Y_TH, Y_T, Y_BUS, Y_X, Y_SW, Y_DR = 104, 150, 222, 252, 282, 326, 362

ctrl, stages = [], []
for d in range(n):
    B = N >> d
    H = B // 2
    a = (SHIFT >> (n - 1 - d)) & 1
    b = SHIFT & (H - 1)
    t = [int(k < b) for k in range(H)]
    swap = [a ^ tk for tk in t]
    drives = [[(j * B + k, j * B + k + H) for j in range(N // B)] for k in range(H)]
    ctrl.append((d, B, H, a, b, t, swap, drives))
    stages.append({"sws": [(u, l, swap[k]) for k in range(H) for u, l in drives[k]]})
assert simulate("ABCDEFGH", stages)[-1] == rotl_ref(list("ABCDEFGH"), SHIFT), "control would not rotate correctly"

W, H_IMG = LM + n * CW + 10, Y_DR + 4 * 19 + 66
out = svg_open(W, H_IMG, f"Control generator of an 8-lane Banyan for shift {SHIFT}: per stage one shift bit a, "
                         "the low bits b, a thermometer decoder and an XOR per switch position")
out.append("""<style>
.bn .bn-cell { fill: var(--surface, #ffffff); stroke: var(--rule, #d3dcd8); stroke-width: 1.2; }
.bn .bn-cell.a { stroke: var(--hi, #b86e00); stroke-width: 2.2; }
.bn .bn-cell.b { fill: var(--accent-soft, #e1eee9); stroke: var(--accent, #0b6b57); stroke-width: 1.6; }
.bn .bn-cv { font-size: 13px; font-weight: 600; text-anchor: middle; dominant-baseline: central; }
.bn .bn-cv.z { fill: var(--muted, #56645f); font-weight: 400; }
.bn .bn-ctl { fill: none; stroke: var(--muted, #56645f); stroke-width: 1.4; }
.bn .bn-ctl.a { stroke: var(--hi, #b86e00); stroke-width: 1.8; }
.bn .bn-dot { fill: var(--hi, #b86e00); }
.bn .bn-drv { font-size: 11.5px; text-anchor: middle; fill: var(--muted, #56645f); }
.bn .bn-drv.x { fill: var(--hi, #b86e00); font-weight: 700; }
.bn .bn-row { font-size: 11.5px; fill: var(--muted, #56645f); dominant-baseline: central; }
</style>""")

for label, yy in (("shift", Y_REG), ("thermometer", Y_TH + 20), ("t[k] = k &lt; b", Y_T), ("a XOR t[k]", Y_X),
                  ("swap[k]", Y_SW), ("drives", Y_DR + 4)):
    out.append(f'<text class="bn-row" x="14" y="{yy}">{label}</text>')

for d, B, H, a, b, t, swap, drives in ctrl:
    cx = LM + d * CW
    kx = [cx + 40 + k * KP for k in range(H)]
    out.append(f'<text class="bn-head" x="{cx + CW / 2 - 20}" y="34">stage {d} · span {H}</text>')
    blocks = (f"{N // B} blocks of {B}: each swap[k] drives {N // B} switches" if N // B > 1
              else f"1 block of {B}: one switch per swap[k]")
    out.append(f'<text class="bn-sub" x="{cx + CW / 2 - 20}" y="54">{blocks}</text>')

    # shift register s[n-1] .. s[0]; bit n-1-d is a, bits below log2(H) are b
    cells = {}
    for i, bit in enumerate(range(n - 1, -1, -1)):
        x = cx + 30 + i * 40
        v = (SHIFT >> bit) & 1
        role = "a" if bit == n - 1 - d else "b" if (1 << bit) < H else ""
        cells[bit] = x + 17
        out.append(f'<rect class="bn-cell {role}" x="{x}" y="{Y_REG - 14}" width="34" height="28" rx="4"/>'
                   f'<text class="bn-cv{"" if role else " z"}" x="{x + 17}" y="{Y_REG}">{v}</text>'
                   f'<text class="bn-sw" x="{x + 17}" y="{Y_REG - 20}">s[{bit}]{" a" if role == "a" else ""}</text>')
    out.append(f'<text class="bn-key" x="{cx + 158}" y="{Y_REG + 4}">a = {a}, b = {b}</text>')

    # thermometer decoder fed by the b bits
    tx0, tx1 = kx[0] - 26, kx[-1] + 26
    for bit, x in cells.items():
        if (1 << bit) < H:
            out.append(f'<path class="bn-ctl" d="M{x} {Y_REG + 14} V{Y_TH}"/>')
    out.append(f'<rect class="bn-box" x="{tx0}" y="{Y_TH}" width="{max(tx1 - tx0, 110)}" height="40" rx="5"/>')
    tlabel = f"k &lt; b, b = {b}" if H > 1 else "b has no bits: t = 0"
    out.append(f'<text class="bn-sw" x="{tx0 + max(tx1 - tx0, 110) / 2}" y="{Y_TH + 24}">{tlabel}</text>')

    # the a wire: down the left of the column, then along a bus over the XORs
    ax = cells[n - 1 - d]
    out.append(f'<path class="bn-ctl a" d="M{ax} {Y_REG + 14} V{Y_REG + 28} H{cx + 12} V{Y_BUS} H{kx[-1] + 20}"/>')
    for k in range(H):
        out.append(f'<path class="bn-ctl" d="M{kx[k]} {Y_TH + 40} V{Y_X - 10}"/>')
        out.append(f'<path class="bn-ctl a" d="M{kx[k] + 20} {Y_BUS} V{Y_X} H{kx[k] + 10}"/>'
                   f'<circle class="bn-dot" cx="{kx[k] + 20}" cy="{Y_BUS}" r="3"/>')
        out.append(f'<circle class="bn-box" cx="{kx[k]}" cy="{Y_X}" r="10"/>'
                   f'<path class="bn-in" d="M{kx[k] - 10} {Y_X} h20 M{kx[k]} {Y_X - 10} v20"/>')
        out.append(f'<path class="bn-ctl" d="M{kx[k]} {Y_X + 10} V{Y_DR - 14}"/>')
        out.append(pill(kx[k], Y_T, str(t[k])))
        out.append(pill(kx[k], Y_SW, str(swap[k])))
        for j, (u, l) in enumerate(drives[k]):
            out.append(f'<text class="bn-drv{" x" if swap[k] else ""}" x="{kx[k]}" y="{Y_DR + 4 + j * 19}">'
                       f'{u}↔{l}</text>')

ky = H_IMG - 26
out.append(f'<text class="bn-key" x="14" y="{ky}">shift = {SHIFT} = {SHIFT:03b}b · orange cell: a = s[n−1−d] · '
           f'tinted cells: b = shift &amp; (span − 1) · bold orange switch: cross (swap = 1)</text>')
out.append("</svg>")
(HERE / "banyan_ctrl8.svg").write_text("\n".join(out) + "\n")
print("wrote banyan_ctrl8.svg: " + " | ".join(f"stage {c[0]} swap={c[6]}" for c in ctrl))
