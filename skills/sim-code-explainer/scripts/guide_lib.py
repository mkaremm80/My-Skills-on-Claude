"""guide_lib - building blocks for colourful "explain-this-code-from-zero" PDF guides.

Typical use (see templates/guide_template.py):

    import sys; sys.path.insert(0, "<skill>/scripts")
    from guide_lib import *
    load_source("my_sim.py")                       # code with  # ==== [BLOCK n] Title ====  markers
    set_meta(title="My Simulator", subtitle="...", tags=[...], cover_image="build/diag/pipeline.png")
    story = start_story()                          # cover + (optional) scope page are added by you
    story += chapter(1, "Python from Zero", "...")
    ...
    build_pdf(story, "My_Guide.pdf")

Every flowable helper returns a LIST of flowables, so always use  story += helper(...).
"""
import os
import re
import hashlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, Image, KeepTogether, CondPageBreak, NextPageTemplate)
from reportlab.platypus.tableofcontents import TableOfContents

try:
    from pygments.lexers import PythonLexer
    from pygments.token import Token
    HAVE_PYGMENTS = True
except ImportError:            # code is still shown, just without colours
    HAVE_PYGMENTS = False

# ------------------------------------------------------------------ fonts (bundled with matplotlib -> portable)
_FD = os.path.join(matplotlib.get_data_path(), "fonts", "ttf") + os.sep
for name, f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
                ("DV-BI", "DejaVuSans-BoldOblique.ttf"), ("DVM", "DejaVuSansMono.ttf"),
                ("DVM-B", "DejaVuSansMono-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, _FD + f))
registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")
registerFontFamily("DVM", normal="DVM", bold="DVM-B", italic="DVM", boldItalic="DVM-B")

# ------------------------------------------------------------------ palette and styles
C = dict(
    navy=colors.HexColor("#1a237e"), blue=colors.HexColor("#1565c0"), teal=colors.HexColor("#00897b"),
    green=colors.HexColor("#2e7d32"), orange=colors.HexColor("#ef6c00"), red=colors.HexColor("#c62828"),
    purple=colors.HexColor("#6a1b9a"), pink=colors.HexColor("#ad1457"), gray=colors.HexColor("#546e7a"),
    dark=colors.HexColor("#212121"), code_bg=colors.HexColor("#eef4fc"), code_ln=colors.HexColor("#d5e3f5"),
)
CHAPTER_COLORS = ["#1a237e", "#00695c", "#4a148c", "#0d47a1", "#e65100", "#2e7d32",
                  "#ad1457", "#283593", "#6a1b9a", "#00838f", "#5d4037", "#37474f"]
_base = dict(fontName="DV", fontSize=10, leading=14.2, textColor=C["dark"])
S = {
    "body": ParagraphStyle("body", alignment=TA_JUSTIFY, spaceAfter=5, **_base),
    "bodyL": ParagraphStyle("bodyL", alignment=TA_LEFT, spaceAfter=3, **_base),
    "small": ParagraphStyle("small", fontName="DV", fontSize=8.6, leading=11.5, textColor=C["dark"]),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=8.5, leading=11, textColor=C["dark"]),
    "cellB": ParagraphStyle("cellB", fontName="DV-B", fontSize=8.6, leading=11, textColor=colors.white),
    "cap": ParagraphStyle("cap", fontName="DV-I", fontSize=8.6, leading=11.5, alignment=TA_CENTER,
                          textColor=C["gray"], spaceAfter=8),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=21, leading=26, textColor=colors.white),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=14.5, leading=19, textColor=C["navy"],
                         spaceBefore=10, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="DV-B", fontSize=11.5, leading=15, textColor=C["blue"],
                         spaceBefore=7, spaceAfter=3),
    "boxtitle": ParagraphStyle("boxtitle", fontName="DV-B", fontSize=9.6, leading=12.5),
    "boxbody": ParagraphStyle("boxbody", fontName="DV", fontSize=9.3, leading=13, alignment=TA_JUSTIFY,
                              textColor=C["dark"], spaceAfter=2),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=7.6, leading=9.6, textColor=C["dark"]),
    "ln": ParagraphStyle("ln", fontName="DVM", fontSize=7, leading=9.6, textColor=C["gray"], alignment=2),
    "toc1": ParagraphStyle("toc1", fontName="DV-B", fontSize=11, leading=17, textColor=C["navy"]),
    "toc2": ParagraphStyle("toc2", fontName="DV", fontSize=9.4, leading=13, leftIndent=16, textColor=C["dark"]),
    "banner": ParagraphStyle("banner", fontName="DV-B", fontSize=11.5, leading=15),
}
PAGE_W = 21.0 * cm - 3.6 * cm      # usable width on A4 with 1.8 cm margins
BUILD_DIR = "build"


# ------------------------------------------------------------------ inline markup
def code_inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<font name="DVM" color="#0d47a1" backColor="#e8eef8">{t}</font>'


def md(text):
    """Mini-markup for all text helpers:  `code`   **bold**   *italic*.
    ReportLab tags also work: <sub>, <super>, <font color=...>, <br/>.
    Write a literal < or & in plain prose as &lt; / &amp;."""
    codes = []

    def keep(m):
        codes.append(code_inline(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"
    t = re.sub(r"`([^`]+)`", keep, text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(\S[^*\n]*?\S|\S)\*(?![\w*])", r"<i>\1</i>", t)
    return re.sub("\x00(\\d+)\x00", lambda m: codes[int(m.group(1))], t)


def para(text, style="body"):
    return [Paragraph(md(text), S[style] if isinstance(style, str) else style)]


def bullets(items, style="body", bullet="▸", color="#1565c0"):
    st = ParagraphStyle("bl", parent=S[style], leftIndent=11, firstLineIndent=-11, alignment=TA_LEFT)
    return [Paragraph(f'<font color="{color}">{bullet}</font> ' + md(it), st) for it in items]


# ------------------------------------------------------------------ coloured call-out boxes
BOX_KINDS = {
    "idea": ("THE IDEA - why are we doing this?", "#2e7d32", "#e8f5e9", "★"),
    "what": ("WHAT IF YOU CHANGE IT?", "#ef6c00", "#fff3e0", "⇄"),
    "warn": ("WATCH OUT - common mistakes", "#c62828", "#ffebee", "!"),
    "model": ("LINK TO THE SYSTEM MODEL", "#6a1b9a", "#f3e5f5", "∑"),
    "py": ("PYTHON CORNER", "#00897b", "#e0f2f1", "⌨"),
    "res": ("WHAT THE RESULT TELLS US", "#1565c0", "#e3f2fd", "↗"),
    "try": ("TRY IT YOURSELF", "#ad1457", "#fce4ec", "✎"),
    "note": ("NOTE", "#546e7a", "#fffde7", "i"),
}


def box(kind, items, title=None):
    """kind: idea | what | warn | model | py | res | try | note.  items: str or list of str/flowables."""
    t, col, bg, icon = BOX_KINDS[kind]
    if isinstance(items, str):
        items = [items]
    content = [Paragraph(f'<font color="{col}">{icon}  {title or t}</font>', S["boxtitle"]), Spacer(1, 3)]
    for it in items:
        content.append(Paragraph(md(it), S["boxbody"]) if isinstance(it, str) else it)
    tb = Table([[content]], colWidths=[PAGE_W - 6])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                            ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor(col)),
                            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return [Spacer(1, 3), tb, Spacer(1, 6)]


def one_liner(text):
    tb = Table([[Paragraph(f'<font color="#1a237e"><b>In one sentence:</b></font> {md(text)}', S["boxbody"])]],
               colWidths=[PAGE_W])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffde7")),
                            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#fbc02d")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return [tb, Spacer(1, 6)]


# ------------------------------------------------------------------ tables, figures, equations
def table(data, col_widths=None, header_color=None, zebra=True, font_size=8.5):
    """data[0] is the header row. Cells are md() strings. col_widths default: equal split."""
    n = len(data[0])
    col_widths = col_widths or [PAGE_W / n] * n
    stc = ParagraphStyle("c", parent=S["cell"], fontSize=font_size, leading=font_size + 2.6)
    rows = [[Paragraph(f"<b>{c}</b>", S["cellB"]) for c in data[0]]]
    for r in data[1:]:
        rows.append([Paragraph(md(str(c)), stc) if not hasattr(c, "wrap") else c for c in r])
    tb = Table(rows, colWidths=col_widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), header_color or C["navy"]),
          ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b0bec5")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if zebra:
        st += [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f5f7fb")) for i in range(2, len(rows), 2)]
    tb.setStyle(TableStyle(st))
    return [tb, Spacer(1, 8)]


def image(path, width_frac=1.0):
    from PIL import Image as PI
    w, h = PI.open(path).size
    W = PAGE_W * width_frac
    maxh = 21 * cm
    if W * h / w > maxh:
        W = maxh * w / h
    return Image(path, width=W, height=W * h / w)


def figure(path, width_frac=1.0, caption=None):
    """Image + caption kept on one page. Missing file -> a red placeholder (never crash the build)."""
    if not os.path.exists(path):
        return box("warn", f"Figure not found: `{path}` (the code did not produce it in this run).")
    out = [image(path, width_frac)]
    if caption:
        out.append(Paragraph(caption, S["cap"]))
    return [KeepTogether(out)]


def side_by_side(left_flowables, right_flowables, left_frac=0.45):
    tb = Table([[left_flowables, right_flowables]], colWidths=[PAGE_W * left_frac, PAGE_W * (1 - left_frac)])
    tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return [tb, Spacer(1, 6)]


def eq(tex, size=13, color="#311b92"):
    """One equation rendered by matplotlib mathtext (a LaTeX subset: no \\begin{cases}, no \\bmod;
    \\frac \\sqrt \\sum \\int \\binom \\mathbf \\mathrm \\hat \\bar \\mathbb \\mathcal Greek all work)."""
    os.makedirs(f"{BUILD_DIR}/eq", exist_ok=True)
    key = hashlib.md5((tex + str(size) + color).encode()).hexdigest()[:12]
    path = f"{BUILD_DIR}/eq/{key}.png"
    if not os.path.exists(path):
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, tex, fontsize=size, color=color)
        try:
            fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
        except ValueError as e:
            plt.close(fig)
            raise ValueError(f"eq(): matplotlib mathtext cannot render {tex!r}. Avoid \\Big, \\text, "
                             f"\\begin{{cases}}, \\bmod (see references/api.md).\n{e}") from None
        plt.close(fig)
    from PIL import Image as PI
    w, h = PI.open(path).size
    wpt, hpt = w * 72 / 300, h * 72 / 300
    if wpt > PAGE_W - 2.4 * cm:
        hpt *= (PAGE_W - 2.4 * cm) / wpt
        wpt = PAGE_W - 2.4 * cm
    im = Image(path, width=wpt, height=hpt)
    im.hAlign = "CENTER"
    return im


def eq_box(tex_list, label=None, size=13):
    """Equations on a soft purple strip with an optional number label such as '(3.2)'."""
    if isinstance(tex_list, str):
        tex_list = [tex_list]
    rows = []
    for t in tex_list:
        rows.append([eq(t, size=size), Paragraph(f'<font color="#6a1b9a">{label or ""}</font>', S["small"])])
        label = None
    tb = Table(rows, colWidths=[PAGE_W - 2.2 * cm, 1.6 * cm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf5fd")),
                            ("ALIGN", (0, 0), (0, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return [tb, Spacer(1, 6)]


# ------------------------------------------------------------------ source code handling
SRC = {"path": None, "lines": [], "blocks": {}}
_MARK = re.compile(r"#\s*=+\s*\[BLOCK\s+(\d+)\]\s*(.+?)\s*=*\s*$")


def load_source(path):
    """Read the code file and find its  # ==== [BLOCK n] Title ====  markers.
    Blocks may be nested inside functions; a block ends where the next one starts."""
    lines = open(path, encoding="utf-8").read().split("\n")
    blocks = {}
    for i, ln in enumerate(lines):
        m = _MARK.search(ln)
        if m:
            blocks[int(m.group(1))] = dict(title=m.group(2), start=i + 1)
    ids = sorted(blocks, key=lambda k: blocks[k]["start"])
    for a, b in zip(ids, ids[1:] + [None]):
        end = blocks[b]["start"] - 1 if b is not None else len(lines)
        while end > blocks[a]["start"] and lines[end - 1].strip() == "":
            end -= 1
        blocks[a]["end"] = end
    SRC.update(path=path, lines=lines, blocks=blocks)
    if not blocks:
        print("WARNING: no BLOCK markers found - run code_parser.py --write-markers first")
    return blocks


def lines(a, b):
    return SRC["lines"][a - 1:b]


def find_line(sub, start=1, end=None):
    """Line number (1-based) of the first line containing `sub`, searching from `start`."""
    end = end or len(SRC["lines"])
    for i in range(start - 1, end):
        if sub in SRC["lines"][i]:
            return i + 1
    raise ValueError(f"find_line: {sub!r} not found between lines {start} and {end}")


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", " ")


_TOK = None


def highlight_line(line):
    if not HAVE_PYGMENTS:
        return _esc(line) or " "
    global _TOK
    if _TOK is None:
        _TOK = [(Token.Comment, "#2e7d32", False), (Token.Literal.String, "#ad1457", False),
                (Token.Literal.Number, "#e65100", False), (Token.Keyword, "#6a1b9a", True),
                (Token.Name.Builtin, "#00838f", False), (Token.Name.Function, "#1565c0", True),
                (Token.Name.Class, "#1565c0", True), (Token.Operator, "#5d4037", False)]
    out = []
    for ttype, val in PythonLexer().get_tokens(line):
        val = val.rstrip("\n")
        if not val:
            continue
        e = _esc(val)
        for tt, c, bold in _TOK:
            if ttype in tt:
                e = f'<font color="{c}">{"<b>" + e + "</b>" if bold else e}</font>'
                break
        out.append(e)
    return "".join(out) or " "


def code_block(code_lines, start_line=1, title=None, highlight_rows=()):
    """Syntax-highlighted code with line numbers; splits across pages row by row."""
    rows = [[Paragraph(str(start_line + i), S["ln"]), Paragraph(highlight_line(ln), S["code"])]
            for i, ln in enumerate(code_lines)]
    tb = Table(rows, colWidths=[0.95 * cm, PAGE_W - 0.95 * cm - 6])
    st = [("BACKGROUND", (1, 0), (1, -1), C["code_bg"]), ("BACKGROUND", (0, 0), (0, -1), C["code_ln"]),
          ("LINEBEFORE", (1, 0), (1, -1), 0.6, C["blue"]), ("TOPPADDING", (0, 0), (-1, -1), 0.4),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 0.4), ("LEFTPADDING", (1, 0), (1, -1), 6),
          ("RIGHTPADDING", (0, 0), (0, -1), 4), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, -1), (-1, -1), 4)]
    st += [("BACKGROUND", (1, r), (1, r), colors.HexColor("#fff59d")) for r in highlight_rows]
    tb.setStyle(TableStyle(st))
    out = []
    if title:
        out += [Paragraph(f'<font color="#1565c0">■</font> <b>{title}</b>', S["small"]), Spacer(1, 2)]
    return out + [tb, Spacer(1, 6)]


def snippet(text, title=None):
    """A small stand-alone example (numbered from 1), e.g. in the Python chapter."""
    return code_block(text.strip("\n").split("\n"), 1, title=title)


def show_block(n, a=None, b=None):
    """The code of block n (or of lines a..b inside it) with the file's real line numbers."""
    blk = SRC["blocks"][n]
    a, b = a or blk["start"], b or blk["end"]
    return code_block(lines(a, b), a)


def line_table(n, rows, a=None, b=None):
    """Line-by-line table for block n. rows = [(substring_of_the_line, explanation_md), ...] in file order.
    The substring locates the line, so explanations survive edits that shift line numbers."""
    blk = SRC["blocks"][n]
    pos, end = a or blk["start"], b or blk["end"]
    out_rows = [[Paragraph("<b>Ln</b>", S["cellB"]), Paragraph("<b>Code</b>", S["cellB"]),
                 Paragraph("<b>What it does / means</b>", S["cellB"])]]
    for sub, expl in rows:
        ln = find_line(sub, pos, end)
        pos = ln
        code = SRC["lines"][ln - 1].strip()
        if "  #" in code and not code.startswith("#"):
            code = code.split("  #")[0].rstrip()
        if len(code) > 46:
            code = code[:44] + " …"
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        out_rows.append([Paragraph(f"<b>{ln}</b>", S["cell"]),
                         Paragraph(f'<font name="DVM" size="7.2" color="#0d47a1">{code}</font>', S["cell"]),
                         Paragraph(md(expl), S["cell"])])
    tb = Table(out_rows, colWidths=[1.0 * cm, 6.2 * cm, PAGE_W - 7.2 * cm], repeatRows=1)
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), C["blue"]),
                            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b0bec5")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#f4f8fd")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (0, -1), 3), ("RIGHTPADDING", (0, 0), (0, -1), 2)]))
    return [Paragraph('<font color="#1565c0">▶</font> <b>Line by line</b>', S["h3"]), tb, Spacer(1, 6)]


# ------------------------------------------------------------------ document structure
META = dict(title="Simulation", subtitle="", kicker="A ZERO-TO-HERO GUIDE", tags=[], cover_image=None,
            companion="", header="", description="")
_key = [0]


def set_meta(**kw):
    """title, subtitle (2 short lines max, use \\n), kicker, tags (list of short strings),
    cover_image (path, e.g. the pipeline diagram), companion (footer text on the cover), header."""
    META.update(kw)
    if not META["header"]:
        META["header"] = META["title"] + "  •  Zero-to-Hero Guide"


def _toc(flowable, level, text):
    _key[0] += 1
    flowable.toc_level, flowable.toc_text, flowable.toc_key = level, text, f"k{_key[0]}"
    return flowable


def chapter(num, title, subtitle=""):
    """Full-width coloured chapter banner on a new page. num=0 or None -> unnumbered."""
    col = colors.HexColor(CHAPTER_COLORS[(num or 0) % len(CHAPTER_COLORS)])
    label = f"CHAPTER {num}" if num else ""
    txt = (f'<font size="10" color="#e3f2fd">{label}</font><br/>' if label else "") + title
    if subtitle:
        txt += f'<br/><font name="DV" size="10" color="#e3f2fd">{subtitle}</font>'
    tb = Table([[Paragraph(txt, S["h1"])]], colWidths=[PAGE_W])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), col), ("LEFTPADDING", (0, 0), (-1, -1), 14),
                            ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                            ("LINEBELOW", (0, 0), (-1, -1), 4, colors.HexColor("#ffca28"))]))
    return [PageBreak(), _toc(tb, 0, (f"{num}. " if num else "") + title), Spacer(1, 10)]


def section(title, toc=True, need=4 * cm):
    """Section heading (level 1 in the table of contents). toc=False before the first chapter.
    need = space that must remain on the page, else start a new page; use need=12*cm when a
    figure follows directly, so the heading is never left alone at the bottom of a page."""
    p = Paragraph(title, S["h2"])
    if toc:
        _toc(p, 1, re.sub("<[^>]+>", "", title))
    return [CondPageBreak(need), p]


def subsection(title):
    return [CondPageBreak(3 * cm), Paragraph(title, S["h3"])]


def block_banner(n):
    """Navy banner 'BLOCK n  Title  (lines a-b)' that also goes into the table of contents."""
    blk = SRC["blocks"][n]
    txt = (f'<font color="#ffca28">BLOCK {n}</font>  <font color="white">{blk["title"]}</font>'
           f'<font color="#bbdefb" size="8.5">   (lines {blk["start"]}–{blk["end"]})</font>')
    tb = Table([[Paragraph(txt, S["banner"])]], colWidths=[PAGE_W])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), C["navy"]), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return [CondPageBreak(7 * cm), Spacer(1, 4), _toc(tb, 1, f"Block {n}: {blk['title']}"), Spacer(1, 6)]


def explain_block(n, summary, line_rows, boxes=(), show_code=True, a=None, b=None):
    """The standard recipe for one block: banner, one-sentence summary, code, line table, boxes.
    boxes = [("idea", "text" or [texts]), ("what", ...), ...]"""
    out = block_banner(n) + one_liner(summary)
    if show_code:
        out += show_block(n, a, b)
    if line_rows:
        out += line_table(n, line_rows, a, b)
    for kind, items in boxes:
        out += box(kind, items)
    return out


def toc_page(title="Contents"):
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"], S["toc2"]]
    return [PageBreak(), Paragraph(title, S["h2"]), Spacer(1, 6), toc]


def legend_page(intro=None):
    """'How to use this guide' page explaining the colour code (no TOC entry)."""
    out = [PageBreak()] + section("How to use this guide", toc=False)
    out += para(intro or "This guide explains a complete simulation program written in Python, assuming **zero "
                         "Python knowledge**. Every page uses the same colours; learn them once:")
    for k, t in [("py", "Explains a **Python** feature the first time it appears. Skip it if you know Python."),
                 ("idea", "The **engineering reason** behind a piece of code."),
                 ("model", "Connects code to an **equation of the system model**."),
                 ("what", "What happens to the **results** if you change a variable."),
                 ("warn", "Typical **mistakes and traps**."),
                 ("res", "Reads a **simulation result** using the numbers of the actual run.")]:
        out += box(k, t)
    out += para("Code is shown in blue boxes with the **real line numbers of the file**, so you can follow along. "
                "Comments are green, keywords purple, numbers orange, text strings pink.")
    return out


def scope_page(included, excluded, statement, note=None):
    """'Scope of this report' page: what the work covers and what it deliberately leaves out."""
    out = [PageBreak()] + section("Scope of this report", toc=False) + para(statement)
    n = max(len(included), len(excluded))
    rows = [["Included in this work", "Deliberately NOT included (outside the scope)"]]
    rows += [[included[i] if i < len(included) else "", excluded[i] if i < len(excluded) else ""] for i in range(n)]
    out += table(rows, [PAGE_W / 2, PAGE_W / 2], header_color=C["teal"])
    if note:
        out += box("note", note, title="IMPORTANT")
    return out


# ------------------------------------------------------------------ page templates
class _Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                         topMargin=2.0 * cm, bottomMargin=1.8 * cm, **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("cover", [fr], onPage=_draw_cover),
                               PageTemplate("normal", [fr], onPageEnd=_draw_page)])
        self.current_chapter = ""

    def beforeDocument(self):
        self.current_chapter = ""

    def afterFlowable(self, f):
        if hasattr(f, "toc_level"):
            self.canv.bookmarkPage(f.toc_key)
            self.canv.addOutlineEntry(f.toc_text, f.toc_key, level=f.toc_level)
            self.notify("TOCEntry", (f.toc_level, f.toc_text, self.page, f.toc_key))
            if f.toc_level == 0:
                self.current_chapter = f.toc_text


def _draw_page(cv, doc):
    w, h = A4
    cv.saveState()
    cv.setFillColor(colors.HexColor("#1a237e"))
    cv.rect(0, h - 0.9 * cm, w, 0.9 * cm, fill=1, stroke=0)
    for i, g in enumerate(["#1565c0", "#00897b", "#6a1b9a", "#ef6c00", "#c62828"]):
        cv.setFillColor(colors.HexColor(g))
        cv.rect(i * w / 5, h - 1.0 * cm, w / 5, 0.1 * cm, fill=1, stroke=0)
    cv.setFillColor(colors.white)
    cv.setFont("DV-B", 8.5)
    cv.drawString(1.8 * cm, h - 0.6 * cm, META["header"][:80])
    cv.setFont("DV", 8.5)
    cv.drawRightString(w - 1.8 * cm, h - 0.6 * cm, doc.current_chapter[:55])
    cv.setFillColor(colors.HexColor("#546e7a"))
    cv.setFont("DV", 8)
    cv.drawCentredString(w / 2, 0.9 * cm, f"—  {doc.page}  —")
    cv.restoreState()


def _wrap(cv, text, font, size, maxw):
    words, lines_, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if cv.stringWidth(t, font, size) > maxw and cur:
            lines_.append(cur)
            cur = wd
        else:
            cur = t
    return lines_ + ([cur] if cur else [])


def _draw_cover(cv, doc):
    w, h = A4
    cv.saveState()
    for i in range(60):                      # navy -> purple gradient
        t = i / 60
        cv.setFillColorRGB(0.10 * (1 - t) + 0.29 * t, 0.14 * (1 - t) + 0.08 * t, 0.49 * (1 - t) + 0.55 * t)
        cv.rect(0, h * (1 - (i + 1) / 60), w, h / 60 + 1, fill=1, stroke=0)
    for i, c in enumerate(["#42a5f5", "#26a69a", "#ab47bc", "#ffa726", "#ef5350", "#66bb6a"]):
        cv.setFillColor(colors.HexColor(c))
        cv.rect(0, h - 5.0 * cm - i * 0.18 * cm, w, 0.12 * cm, fill=1, stroke=0)
    cv.setFillColor(colors.white)
    cv.setFont("DV-B", 13)
    cv.drawString(2 * cm, h - 3.0 * cm, META["kicker"])
    y = h - 7.4 * cm
    size = 30 if len(META["title"]) < 24 else 24
    for ln in _wrap(cv, META["title"], "DV-B", size, w - 4 * cm):
        cv.setFont("DV-B", size)
        cv.drawString(2 * cm, y, ln)
        y -= size * 1.2
    cv.setFillColor(colors.HexColor("#bbdefb"))
    for part in META["subtitle"].split("\n"):
        for ln in _wrap(cv, part, "DV", 13, w - 4 * cm):
            cv.setFont("DV", 13)
            cv.drawString(2 * cm, y - 6, ln)
            y -= 18
    img = META.get("cover_image")
    if img and os.path.exists(img):
        from PIL import Image as PI
        iw, ih = PI.open(img).size
        W = w - 3.2 * cm
        H = min(W * ih / iw, y - 6.5 * cm)
        W = H * iw / ih
        cv.drawImage(img, (w - W) / 2, y - 1.0 * cm - H, width=W, height=H, mask="auto")
    x, yy = 2 * cm, 4.6 * cm
    cols = ["#42a5f5", "#26a69a", "#ab47bc", "#ffa726", "#ef5350", "#66bb6a"]
    cv.setFont("DV-B", 9)
    for i, t in enumerate(META["tags"]):
        tw = cv.stringWidth(t, "DV-B", 9) + 14
        if x + tw > w - 2 * cm:
            x, yy = 2 * cm, yy - 0.85 * cm
        cv.setFillColor(colors.HexColor(cols[i % len(cols)]))
        cv.roundRect(x, yy, tw, 0.6 * cm, 5, fill=1, stroke=0)
        cv.setFillColor(colors.white)
        cv.drawString(x + 7, yy + 0.19 * cm, t)
        x += tw + 8
    cv.setFont("DV", 9)
    cv.setFillColor(colors.HexColor("#c5cae9"))
    cv.drawString(2 * cm, 1.8 * cm, META["companion"])
    cv.restoreState()


def start_story():
    """Begin the story: the cover page (drawn from META) and the switch to normal pages."""
    return [Spacer(1, 1), NextPageTemplate("normal")]


def build_pdf(story, out_path):
    os.makedirs(BUILD_DIR, exist_ok=True)
    doc = _Doc(out_path, title=META["title"], author="sim-code-explainer")
    doc.multiBuild(story)
    print("written", out_path)
    return out_path


# ------------------------------------------------------------------ result helpers
def crossing(x, y, target, log=True):
    """x where curve y first crosses `target` (e.g. SNR at BER=1e-3). None if never crossed."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    for i in range(len(y) - 1):
        if np.isnan(y[i]) or np.isnan(y[i + 1]):
            continue
        y0, y1 = (np.log10(y[i]), np.log10(y[i + 1])) if log and y[i] > 0 and y[i + 1] > 0 else (y[i], y[i + 1])
        t = np.log10(target) if log and target > 0 else target
        if (y0 - t) * (y1 - t) <= 0 and y0 != y1:
            return x[i] + (t - y0) / (y1 - y0) * (x[i + 1] - x[i])
    return None


def sci(v, digits=1):
    """1.2x10^-3 formatting for paragraphs."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "n/a"
    if v == 0:
        return "0"
    e = int(np.floor(np.log10(abs(v))))
    return f"{v / 10 ** e:.{digits}f}×10<super>{e}</super>"


# ------------------------------------------------------------------ Python-from-zero chapter (auto)
def python_chapter(features, num=1, uses=None, intro=None):
    """Build the 'Python from Zero' chapter from the feature ids detected by code_parser.py.
    uses: optional {feature_id: "where it is used in THIS code"} to tie each lesson to the program."""
    from python_catalog import CATALOG, ORDER
    uses = uses or {}
    out = chapter(num, "Python from Zero", "only what this program needs — nothing more")
    out += para(intro or "Python is a programming language that reads almost like English. A program is a text file "
                         "(`.py`) executed from top to bottom. In **Google Colab** the program is split into **cells**; "
                         "run a cell with **Shift + Enter**. This chapter teaches only the Python features that "
                         "appear in the program explained in this guide.")
    k = 0
    for fid in ORDER:
        if fid not in features or fid not in CATALOG:
            continue
        k += 1
        e = CATALOG[fid]
        out += section(f"{num}.{k}  {e['title']}")
        out += para(e["text"])
        if e.get("code"):
            out += snippet(e["code"])
        if e.get("tip"):
            out += box("py", e["tip"])
        if fid in uses:
            out += box("note", f"**In this program:** {uses[fid]}", title="WHERE YOU WILL SEE IT")
    out += box("note", "**Reading an error message:** Python prints a *Traceback*. Read it from the **bottom**: "
                       "the last line says what went wrong, the lines above say where. Print the variables "
                       "involved (and `x.shape` for arrays) to debug.")
    return out
