"""Draw figures/hybrid9.svg: a scale model of the paper's hybrid network.
The 802.11n network is one 3x3 IBN stage over three 27-lane barrel EUs
(81 = 3 x 27); here the same structure is drawn at 9 = 3 x 3, rotating A..I
left by SHIFT. The EUs are drawn as dashed sub-networks (each is a small
barrel rotator driven directly by the bits of b).

Checked against the reference rotation, with each EU modelled by rotl_barrel.

    python3 make_hybrid9.py          (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_barrel, rotl_ref  # noqa: E402
from switchfig import draw, simulate  # noqa: E402

P, SHIFT = 3, 5                                  # EU size, shift
N = 3 * P
a, b = SHIFT // P, SHIFT % P
r = [(a + (k < b)) % 3 for k in range(P)]

stages = [{"title": "IBN stage: 3×3", "sub": f"a={a} b={b} → r = (a + (k&lt;b)) mod 3",
           "sws": [((k, k + P, k + 2 * P), r[k]) for k in range(P)]},
          {"title": f"three {P}-lane EUs", "sub": f"each rotl by b = {b}", "box_w": 150,
           "sws": [((q * P, q * P + 1, q * P + 2), b) for q in range(3)],
           "inner": {q: [f"EU {q}: {P}-lane barrel", f"rotl by b = {b}", "select = bits of b"]
                     for q in range(3)}}]

values = simulate("ABCDEFGHI", stages)
eus = sum((rotl_barrel(values[1][q * P:(q + 1) * P], b) for q in range(3)), [])
assert values[-1] == eus == rotl_ref(values[0], SHIFT), "figure would not match"

svg = draw(stages, values, stage_w=240, out_sub=f"in[(i+{SHIFT}) mod {N}]",
           note=f"3×3: out port q ← in port (q + r) mod 3 · s = {SHIFT} = {a}·{P} + {b} · "
                "802.11n: 81 = 3 × 27",
           key=False,
           aria=f"Hybrid network scale model: one 3x3 IBN stage over three {P}-lane barrel EUs, "
                f"rotating A to I left by {SHIFT}")
(HERE / "hybrid9.svg").write_text(svg)
print(f"wrote hybrid9.svg: {' '.join(values[0])} -> {' '.join(values[1])} -> {' '.join(values[-1])}  (r = {r})")
