"""Draw figures/benes8.svg: an 8-lane Benes network (5 stages of 2x2 switches)
routing A..H into bit-reversed order, a permutation a Banyan cannot make.

The switch settings come from the looping algorithm below; the result is
simulated stage by stage and checked before anything is drawn.

    python3 make_benes8.py           (run from this folder)
"""
from pathlib import Path

from switchfig import draw, simulate

HERE = Path(__file__).resolve().parent
N = 8
n = N.bit_length() - 1
S = 2 * n - 1                                   # 5 stages


def span(d):
    """Benes = Banyan (spans 4, 2, 1) + mirrored Banyan (2, 4), sharing the middle stage."""
    return N >> (min(d, S - 1 - d) + 1)


def route(src, dst, base, t, setting):
    """Looping algorithm. src: values entering stage t on lanes base.., dst: the
    values wanted on those lanes after stage S-1-t. Fills setting[(stage, U)]."""
    m = len(src)
    if m == 2:                                  # the middle stage: one switch
        setting[(t, base)] = src[0] != dst[0]
        return
    h = m // 2
    in_sw = {v: i % h for i, v in enumerate(src)}       # which input switch holds v
    out_sw = {v: i % h for i, v in enumerate(dst)}      # which output switch wants v
    in_mate = {src[k]: src[k + h] for k in range(h)} | {src[k + h]: src[k] for k in range(h)}
    out_mate = {dst[k]: dst[k + h] for k in range(h)} | {dst[k + h]: dst[k] for k in range(h)}

    up = {}                                     # True: through the upper sub-network
    for start in src:
        if start in up:
            continue
        v = start
        while v not in up:                      # follow one loop of constraints
            up[v] = True
            w = in_mate[v]                      # shares v's input switch: must go down
            up[w] = False
            v = out_mate[w]                     # shares w's output switch: must go up
        assert up[v], "looping algorithm hit an odd cycle"

    sub_src = {True: [None] * h, False: [None] * h}
    sub_dst = {True: [None] * h, False: [None] * h}
    for k in range(h):
        setting[(t, base + k)] = not up[src[k]]                 # cross sends src[k] down
        sub_src[up[src[k]]][k] = src[k]
        sub_src[up[src[k + h]]][k] = src[k + h]
        setting[(S - 1 - t, base + k)] = not up[dst[k]]         # cross takes lane k from below
        sub_dst[up[dst[k]]][k] = dst[k]
        sub_dst[up[dst[k + h]]][k] = dst[k + h]
    route(sub_src[True], sub_dst[True], base, t + 1, setting)
    route(sub_src[False], sub_dst[False], base + h, t + 1, setting)


def bitrev(i):
    return int(f"{i:0{n}b}"[::-1], 2)


src = list("ABCDEFGH")
dst = [src[bitrev(i)] for i in range(N)]        # A E C G B F D H

setting = {}
route(src, dst, 0, 0, setting)
stages = []
for d in range(S):
    H = span(d)
    B = 2 * H
    sws = [(j * B + k, j * B + k + H, int(setting[(d, j * B + k)]))
           for j in range(N // B) for k in range(H)]
    part = "input column" if d == 0 else "output column" if d == S - 1 else ""
    stages.append({"title": f"stage {d} · span {H}", "sub": part, "sws": sws})

values = simulate(src, stages)
assert values[-1] == dst, "figure would not match the requested permutation"

svg = draw(stages, values, stage_w=150, out_sub="bit-reversed",
           note="settings found by the looping algorithm (make_benes8.py), not by a simple rule",
           groups=[(1, 3, 0, 3, "upper 4-lane Benes"), (1, 3, 4, 7, "lower 4-lane Benes")],
           aria="8-lane Benes network, 5 stages of four 2x2 switches, routing A to H into bit-reversed order")
(HERE / "benes8.svg").write_text(svg)
print(f"wrote benes8.svg: {' '.join(values[0])} -> {' '.join(values[-1])}")
