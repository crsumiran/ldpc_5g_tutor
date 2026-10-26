"""Build one HTML page from hw_tutorial/*.md plus source listings."""
import html
import re
import sys
from pathlib import Path

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
TEMPLATE = Path(__file__).with_name("template.html").read_text()

CHAPTERS = [
    ("README.md", "intro", "Start here"),
    ("00_the_application.md", "ch00", "The application"),
    ("01_ldpc_for_rtl_engineers.md", "ch01", "LDPC for RTL engineers"),
    ("02_why_rotation.md", "ch02", "Why rotation?"),
    ("03_switching_basics.md", "ch03", "Switching basics"),
    ("04_barrel_rotator.md", "ch04", "The barrel rotator"),
    ("05_variable_size_qsn.md", "ch05", "Variable Z: QSN"),
    ("06_banyan_ibn_5g.md", "ch06", "Banyan, IBN, 5G"),
    ("07_decoder_architecture.md", "ch07", "Decoder architecture"),
    ("08_build_plan.md", "ch08", "Build and verify plan"),
    ("09_reading_guide.md", "ch09", "Reading guide"),
    ("glossary.md", "glossary", "Glossary"),
]
FILE_TO_ID = {f: cid for f, cid, _ in CHAPTERS}
LISTINGS = ["rtl/switches.v", "rtl/rot_barrel.v", "rtl/rot_qsn.v", "rtl/rot_banyan.v",
            "rtl/rot_ibn3.v", "rtl/rot_5g.v", "tb/tb_rotators.v",
            "model/rotators.py", "model/layered_qc.py", "run_tests.sh"]

FMT = HtmlFormatter(nowrap=True)


def code_block(lang, body):
    try:
        lexer = get_lexer_by_name(lang)
        inner = highlight(body, lexer, FMT)
    except Exception:
        inner = html.escape(body)
    return f'<div class="code"><pre><code>{inner}</code></pre></div>'


def preprocess(text):
    # fenced code -> placeholders (mermaid gets its own element)
    blocks = []

    def fence(m):
        lang, body = m.group(1).strip(), m.group(2)
        if lang == "mermaid":
            out = f'<pre class="mermaid">{html.escape(body)}</pre>'
        else:
            out = code_block(lang or "text", body)
        blocks.append(out)
        return f"\n\nCODEBLOCK{len(blocks) - 1}END\n\n"

    text = re.sub(r"^```([^\n]*)\n(.*?)^```\s*$", fence, text, flags=re.S | re.M)
    text = text.replace("<details>", '<details markdown="1">')
    text = re.sub(r"<summary>(.*?)</summary>", lambda m: f"<summary>{m.group(1)}</summary>\n", text)
    return text, blocks


def fix_links(h):
    def repl(m):
        target = m.group(1)
        name = target.split("#")[0]
        if name in FILE_TO_ID:
            return f'href="#{FILE_TO_ID[name]}"'
        return m.group(0)
    return re.sub(r'href="([^"]+?\.md)"', repl, h)


def render(md_text, prefix):
    text, blocks = preprocess(md_text)
    conv = markdown.Markdown(
        extensions=["tables", "md_in_html", "toc", "sane_lists"],
        extension_configs={"toc": {"slugify": lambda v, sep: prefix + "-" + re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-")}},
    )
    h = conv.convert(text)
    for i, b in enumerate(blocks):
        h = h.replace(f"<p>CODEBLOCK{i}END</p>", b).replace(f"CODEBLOCK{i}END", b)
    h = re.sub(r"<table>", '<div class="table"><table>', h)
    h = h.replace("</table>", "</table></div>")
    h = h.replace('<input type="checkbox"', '<input type="checkbox" disabled')
    h = re.sub(r'<p><img alt="([^"]*)" src="(figures/[^"]+\.svg)" /></p>', inline_svg, h)
    return fix_links(h)


def inline_svg(m):
    # Inline the SVG (instead of <img>) so it follows the page's light/dark tokens.
    svg = (SRC / m.group(2)).read_text()
    return (f'<figure class="fig"><div class="fig-scroll">{svg}</div>'
            f'<figcaption>{m.group(1)}</figcaption></figure>')


sections, nav = [], []
for fname, cid, label in CHAPTERS:
    md = (SRC / fname).read_text()
    if fname == "README.md":
        # the page header replaces the README's H1 and opening line
        md = re.sub(r"^# .*\n", "", md, count=1)
    body = render(md, cid)
    num = cid[2:] if cid.startswith("ch") else ""
    nav.append(f'<li><a href="#{cid}"><span class="n">{num}</span>{html.escape(label)}</a></li>')
    sections.append(f'<section class="chapter" id="{cid}">{body}</section>')
    if fname == "README.md":
        sections.append("<!--WIDGET-->")
        nav.append('<li><a href="#lab"><span class="n">▸</span>Rotator lab</a></li>')

listings = []
for rel in LISTINGS:
    p = SRC / rel
    lang = {"v": "verilog", "py": "python", "sh": "bash"}[p.suffix[1:]]
    n = len(p.read_text().splitlines())
    listings.append(f'<details class="listing"><summary><code>{rel}</code> <span class="lines">{n} lines</span></summary>'
                    f'{code_block(lang, p.read_text())}</details>')
nav.append('<li><a href="#sources"><span class="n">A</span>Source listings</a></li>')
sections.append('<section class="chapter" id="sources"><h1>Appendix · Source listings</h1>'
                '<p>The complete RTL, testbench and golden models from <code>hw_tutorial/</code>. '
                'Run <code>./run_tests.sh</code> in that folder to check all of them.</p>'
                + "".join(listings) + "</section>")

page = TEMPLATE.replace("<!--NAV-->", "\n".join(nav)).replace("<!--CONTENT-->", "\n".join(sections))
page = page.replace("<!--WIDGET-->", Path(__file__).with_name("widget.html").read_text())
if "--standalone" in sys.argv:
    # The claude.ai viewer supplies the document skeleton and renders mermaid;
    # a plain local file has to do both itself.
    head, body = page.split("</style>", 1)
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + head + '</style>\n</head>\n<body>\n' + body +
            '\n<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>\n'
            '<script>if (window.mermaid) mermaid.initialize({ startOnLoad: true, theme: '
            'matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "neutral" });</script>\n'
            '</body>\n</html>\n')
OUT.write_text(page)
print(f"wrote {OUT} ({len(page) // 1024} KiB)")
