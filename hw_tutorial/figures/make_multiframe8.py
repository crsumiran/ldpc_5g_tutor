"""Draw figures/multiframe8.svg: an 8-lane Banyan in multi-frame mode. Stage 0
is forced to bar, so the network splits into two independent 4-lane rotators,
each with its own shift.

Checked against rotl_banyan_multiframe and the reference rotation of each frame.

    python3 make_multiframe8.py      (run from this folder)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "model"))
from rotators import rotl_banyan_multiframe, rotl_ref  # noqa: E402
from switchfig import draw, simulate  # noqa: E402

N, F = 8, 2                                     # lanes, frames
SHIFTS = [1, 3]                                 # one shift per frame
size = N // F
m = size.bit_length() - 1

stages = [{"title": "stage 0 · span 4", "sub": "forced bar",
           "sws": [(k, k + N // 2, 0) for k in range(N // 2)]}]
for d in range(m):
    B = size >> d
    H = B // 2
    sws = []
    for j, s in enumerate(SHIFTS):              # every frame gets its own control
        a = (s >> (m - 1 - d)) & 1
        b = s & (H - 1)
        base = j * size
        for blk in range(size // B):
            sws += [(base + blk * B + k, base + blk * B + k + H, a ^ (k < b)) for k in range(H)]
    stages.append({"title": f"stage {d + 1} · span {H}", "sub": "", "sws": sws})

values = simulate("ABCDEFGH", stages)
expect = sum((rotl_ref(list("ABCDEFGH")[j * size:(j + 1) * size], s) for j, s in enumerate(SHIFTS)), [])
assert values[-1] == expect == rotl_banyan_multiframe(values[0], SHIFTS), "figure would not match"

svg = draw(stages, values, stage_w=200, out_sub="each frame rotated",
           note="stages 1–2: each frame's switches are driven by its own shift (a XOR (k &lt; b) per frame)",
           groups=[(1, m, 0, size - 1, f"frame 0 · 4-lane rotator · shift {SHIFTS[0]}"),
                   (1, m, size, N - 1, f"frame 1 · 4-lane rotator · shift {SHIFTS[1]}")],
           aria=f"8-lane Banyan in multi-frame mode: stage 0 forced to bar, two 4-lane frames rotated by "
                f"{SHIFTS[0]} and {SHIFTS[1]}")
(HERE / "multiframe8.svg").write_text(svg)
print(f"wrote multiframe8.svg: {' '.join(values[0])} -> {' '.join(values[-1])}")
