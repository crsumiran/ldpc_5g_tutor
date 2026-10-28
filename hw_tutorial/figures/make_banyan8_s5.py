"""Draw figures/banyan8_s5.svg: the chapter 06 section 3 worked example, an
8-lane Banyan rotating A..H left by 5, with all three stages expanded and the
sub-rotators of each recursion level shaded.

Switch settings follow rtl/rot_banyan.v. Checked against rotl_banyan's trace
and the reference rotation.

    python3 make_banyan8_s5.py       (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_banyan, rotl_ref  # noqa: E402
from switchfig import draw, simulate  # noqa: E402

N, SHIFT = 8, 5
n = N.bit_length() - 1

stages = []
for d in range(n):
    B = N >> d
    H = B // 2
    a = (SHIFT >> (n - 1 - d)) & 1
    b = SHIFT & (H - 1)
    swap = [a ^ (k < b) for k in range(H)]
    sws = [(j * B + k, j * B + k + H, swap[k]) for j in range(N // B) for k in range(H)]
    stages.append({"title": f"stage {d} · span {H}",
                   "sub": f"a={a} b={b} → swap=[{','.join(map(str, swap))}]", "sws": sws})

values = simulate("ABCDEFGH", stages)
assert values[-1] == rotl_ref(values[0], SHIFT) == rotl_banyan(values[0], SHIFT), "figure would not match"
assert values[1] == list("AFGHEBCD") and values[2] == list("GFAHCBED"), "text trace would not match"

svg = draw(stages, values, stage_w=200, out_sub=f"in[(i+{SHIFT}) mod 8]",
           note=f"shift = {SHIFT} = {SHIFT:03b}b · stage d uses a = shift bit (2 − d), b = shift mod span",
           groups=[(1, 2, 0, 3, ""), (1, 2, 4, 7, "shaded: the two 4-lane rotators of stage 0's split, each rotl by b = 1")],
           aria=f"8-lane Banyan network rotating A to H left by {SHIFT}, all three stages expanded")
(HERE / "banyan8_s5.svg").write_text(svg)
print("wrote banyan8_s5.svg: " + " -> ".join("".join(v) for v in values))
