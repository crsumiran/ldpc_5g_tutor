"""Draw figures/ibn12.svg: a 12-lane Improved Banyan Network (Song et al. 2022)
rotating A..L left by SHIFT: one column of 3x3 rotating switches, then three
4-lane Banyans that all rotate by the same b.

Switch settings follow rtl/rot_ibn3.v and rtl/rot_banyan.v. The result is
checked against the reference rotation and the rotl_ibn model before drawing.

    python3 make_ibn12.py            (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_ibn, rotl_ref  # noqa: E402
from switchfig import draw, simulate  # noqa: E402

M, SHIFT = 4, 7
N = 3 * M
n = M.bit_length() - 1
a, b = SHIFT // M, SHIFT % M                    # a = top bits (0..2), b = low bits

# 3x3 stage: switch k joins lanes k, k+M, k+2M and rotates the blocks by r_k
r = [(a + (k < b)) % 3 for k in range(M)]
stages = [{"title": "3×3 stage", "sub": f"a={a} b={b} → r = (a + (k&lt;b)) mod 3",
           "sws": [((k, k + M, k + 2 * M), r[k]) for k in range(M)]}]

# then three M-lane Banyans, every one rotating by b with the same control
for d in range(n):
    B = M >> d
    H = B // 2
    ad = (b >> (n - 1 - d)) & 1
    bd = b & (H - 1)
    sws = [(j * B + k, j * B + k + H, ad ^ (k < bd)) for j in range(N // B) for k in range(H)]
    stages.append({"title": f"Banyan stage {d} · span {H}", "sub": f"a={ad} b={bd} · all 3 blocks",
                   "sws": sws})

values = simulate("ABCDEFGHIJKL", stages)
assert values[-1] == rotl_ref(values[0], SHIFT) == rotl_ibn(values[0], SHIFT), "figure would not match"

blocks = [(1, n, q * M, q * M + M - 1, f"three 4-lane Banyans, each rotl by b = {b}" if q == 2 else "")
          for q in range(3)]
svg = draw(stages, values, stage_w=210, out_sub=f"in[(i+{SHIFT}) mod {N}]",
           note=f"3×3 switch: output port q takes input port (q + r) mod 3 · shift = {SHIFT} = {a}·{M} + {b}",
           groups=blocks,
           aria=f"12-lane improved Banyan network: a 3x3 switch stage and three 4-lane Banyans, rotating A to L left by {SHIFT}")
(HERE / "ibn12.svg").write_text(svg)
print(f"wrote ibn12.svg: {' '.join(values[0])} -> {' '.join(values[-1])}  (r = {r})")
