"""Draw figures/banyan_split8.svg: one level of the Banyan recursion at N = 8,
s = 5. Stage 0 (four 2x2 switches) sorts the values into the half where they
must end up; each half is then a 4-lane rotator that rotates left by
b = s mod 4. The halves are drawn as dashed outlines because each stands for
two stages of 2x2 switches, not a 4x4 switch. This is the picture behind the
derivation in chapter 06 section 2.

Checked against rotl_banyan and the reference rotation.

    python3 make_banyan_split8.py    (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_banyan, rotl_ref  # noqa: E402
from switchfig import draw, simulate  # noqa: E402

N, SHIFT = 8, 5
H = N // 2
a, b = SHIFT // H, SHIFT % H
swap = [a ^ (k < b) for k in range(H)]

stages = [{"title": "stage 0 · span 4", "sub": f"a={a} b={b} → swap = [{','.join(map(str, swap))}]",
           "sws": [(k, k + H, swap[k]) for k in range(H)]},
          {"title": f"two {H}-lane rotators", "sub": f"both rotl by b = {b}",
           "sws": [((0, 1, 2, 3), b), ((4, 5, 6, 7), b)],
           "box_w": 150,
           "inner": {q: [f"{H}-lane rotator", f"rotl by b = {b}", "", "inside: 2 stages", "of 2×2 switches",
                         "(opened up in §3)"] for q in range(2)}}]

values = simulate("ABCDEFGH", stages)
assert values[-1] == rotl_ref(values[0], SHIFT) == rotl_banyan(values[0], SHIFT), "figure would not match"
# the boxes hide two real stages: check them as well
assert rotl_banyan(values[1][:H], b) == values[-1][:H] and rotl_banyan(values[1][H:], b) == values[-1][H:]
# what the text claims: the upper half holds exactly the values output lanes 0-3 need
assert sorted(values[1][:H]) == sorted(values[-1][:H]) and values[1][:H] == list("AFGH")

svg = draw(stages, values, stage_w=230, out_sub=f"in[(i+{SHIFT}) mod 8]",
           note=f"s = {SHIFT} = a·4 + b · a = {a}, b = {b} · swap[k] = a XOR (k &lt; b)",
           groups=[(1, 1, 0, H - 1, ""), (1, 1, H, N - 1, "")],
           aria=f"One level of the 8-lane Banyan recursion: stage 0 sorts A to H into halves, then two "
                f"4-lane rotators each rotate left by {b}, giving a left rotation by {SHIFT}")
(HERE / "banyan_split8.svg").write_text(svg)
print(f"wrote banyan_split8.svg: {' '.join(values[0])} -> {' '.join(values[1])} -> {' '.join(values[-1])}")
