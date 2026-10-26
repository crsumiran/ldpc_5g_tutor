"""Shared SVG pieces for the mux-level figures (barrel rotator, QSN).

A 2:1 mux is drawn as a trapezoid: input 0 enters at the upper port, input 1
at the lower port, and the output leaves on the right at the lane's height.
The wire the select actually picks is drawn solid; the other one is faint.
Colours are the page's theme tokens with light-theme fallbacks (see switchfig.py).
"""
from switchfig import STYLE

MW, PORT = 26, 8                      # mux width, port offset from the lane line

MUX_STYLE = """<style>
.bn .bn-mux { fill: var(--surface, #ffffff); stroke: var(--ink, #15211d); stroke-width: 1.4; }
.bn .bn-mux.x { fill: var(--accent-soft, #e1eee9); stroke: var(--hi, #b86e00); stroke-width: 2; }
.bn .bn-sel { font-size: 10.5px; font-weight: 600; text-anchor: middle; dominant-baseline: central; }
.bn .bn-on { fill: none; stroke: var(--accent, #0b6b57); stroke-width: 2.2; }
.bn .bn-off { fill: none; stroke: var(--muted, #56645f); stroke-width: 1.1; opacity: 0.35; }
.bn .bn-dash { stroke-dasharray: 6 4; }
.bn .bn-pill.z { stroke: var(--rule, #d3dcd8); }
.bn .bn-val.z { fill: var(--muted, #56645f); font-weight: 400; }
.bn .bn-zero { font-size: 10.5px; fill: var(--muted, #56645f); text-anchor: end; dominant-baseline: central; }
.bn .bn-panel { font-size: 12.5px; font-weight: 600; fill: var(--accent, #0b6b57); }
</style>"""


def svg_open(W, H, aria):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" class="bn" '
            f'role="img" aria-label="{aria}">', STYLE, MUX_STYLE,
            f'<rect class="bn-bg" x="0" y="0" width="{W}" height="{H}" rx="8"/>']


def wire(x1, y1, x2, y2, on, dashed=False):
    mx = (x1 + x2) / 2
    cls = ("bn-on" if on else "bn-off") + (" bn-dash" if dashed else "")
    return f'<path class="{cls}" d="M{x1} {y1} C{mx} {y1} {mx} {y2} {x2} {y2}"/>'


def mux(x, y, label, hi=False):
    """Trapezoid with inputs at (x, y -/+ PORT) and output at (x + MW, y)."""
    cls = "bn-mux x" if hi else "bn-mux"
    return (f'<path class="{cls}" d="M{x} {y - 15} L{x + MW} {y - 9} L{x + MW} {y + 9} L{x} {y + 15} Z"/>'
            f'<text class="bn-sel" x="{x + MW / 2}" y="{y}">{label}</text>')


def pill(x, y, v):
    z = " z" if v in ("0", "·") else ""
    return (f'<circle class="bn-pill{z}" cx="{x}" cy="{y}" r="12"/>'
            f'<text class="bn-val{z}" x="{x}" y="{y}">{v}</text>')


def zero_in(x, y):
    """A constant-0 input: a short stub with a 0 in front of it."""
    return f'<path class="bn-off" d="M{x - 14} {y} H{x}"/><text class="bn-zero" x="{x - 17}" y="{y}">0</text>'


def legend(x, y, note, note_below=False):
    return (mux(x, y, "0") + f'<text class="bn-key" x="{x + MW + 8}" y="{y + 4}">select 0: upper input</text>'
            + mux(x + 190, y, "1", hi=True)
            + f'<text class="bn-key" x="{x + 190 + MW + 8}" y="{y + 4}">select 1: lower input</text>'
            + f'<path class="bn-on" d="M{x + 390} {y} h26"/>'
            f'<text class="bn-key" x="{x + 422}" y="{y + 4}">selected wire</text>'
            + (f'<text class="bn-key" x="{x}" y="{y + 34}">{note}</text>' if note_below else
               f'<text class="bn-key" x="{x + 530}" y="{y + 4}">{note}</text>'))
