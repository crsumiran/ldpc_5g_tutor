"""Draw figures/banyan8.svg: an 8-lane Banyan rotator (3 stages of 2x2 switches)
carrying A..H through a left rotation by SHIFT.

The switch settings come from the same rule as rtl/rot_banyan.v, and the
result is checked against the reference rotation before anything is drawn.

    python3 make_banyan8.py          (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_ref  # noqa: E402
from switchfig import draw, simulate  # noqa: E402

N, SHIFT = 8, 3
n = N.bit_length() - 1

stages = []
for d in range(n):
    B = N >> d
    H = B // 2
    a = (SHIFT >> (n - 1 - d)) & 1        # same control rule as rot_banyan.v
    b = SHIFT & (H - 1)
    sws = [(j * B + k, j * B + k + H, a ^ (k < b)) for j in range(N // B) for k in range(H)]
    rule = ("all cross" if (a and b == 0) else "all bar" if b == 0 else
            f"k&lt;{b} {'bar' if a else 'cross'}, rest {'cross' if a else 'bar'}")
    stages.append({"title": f"stage {d} · span {H}", "sub": f"a={a} b={b} → {rule}", "sws": sws})

values = simulate("ABCDEFGH", stages)
assert values[-1] == rotl_ref(values[0], SHIFT), "figure would not match the reference"

svg = draw(stages, values, stage_w=200, out_sub=f"in[(i+{SHIFT}) mod 8]",
           note=f"shift = {SHIFT} = {SHIFT:03b}b · a = one shift bit, b = shift mod span · "
                "swap[k] = a XOR (k &lt; b)",
           aria=f"8-lane Banyan network, 3 stages of four 2x2 switches, rotating A to H left by {SHIFT}")
(HERE / "banyan8.svg").write_text(svg)
print(f"wrote banyan8.svg: {' '.join(values[0])} -> {' '.join(values[-1])}")
