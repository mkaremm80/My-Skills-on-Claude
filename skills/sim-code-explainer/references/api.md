# guide_lib / diagram_kit API

Import in `make_guide.py`:
```python
import sys, os; sys.path.insert(0, os.path.join(SKILL, "scripts"))
from guide_lib import *
from diagram_kit import pipeline, loop_flow, boxes_row
```
Every helper that produces content returns a **list of flowables**: always `story += helper(...)`.

## Text markup (all text arguments)
`` `code` `` inline code - `**bold**` - `*italic*` - ReportLab tags `<sub>`, `<super>`, `<font color="#c62828">`,
`<br/>`. A literal `<` or `&` in prose must be written `&lt;` / `&amp;` (inside backticks it is escaped for you).
Do not use Unicode subscript/superscript digits (they render as boxes); use `<sub>`/`<super>`.

## Source code
| function | purpose |
|---|---|
| `load_source(path)` | read the block-marked program; fills `SRC["blocks"]` = {n: {title, start, end}} |
| `show_block(n, a=None, b=None)` | code of block n (or of lines a..b) with real line numbers, syntax colours |
| `line_table(n, rows, a=None, b=None)` | rows = `[(substring_on_line, explanation), ...]` **in file order**; the substring finds the line, so tables survive line shifts. Raises if a substring is not found (fix the substring) |
| `explain_block(n, summary, rows, boxes=[(kind, text_or_list), ...], show_code=True, a=None, b=None)` | banner + one-liner + code + line table + boxes: the standard recipe |
| `find_line(sub, start=1)` | line number of the first line containing `sub` - use it in prose ("line {find_line('dt =')}") |
| `snippet(text, title=None)` | small stand-alone example numbered from 1 |
| `code_block(list_of_lines, start_line)` | arbitrary code lines |

## Structure
| function | purpose |
|---|---|
| `set_meta(title, subtitle, tags, cover_image, companion, kicker, header)` | cover page + running header |
| `start_story()` | first items of the story (cover page) |
| `scope_page(included, excluded, statement, note)` | "Scope of this report" page |
| `legend_page(intro=None)` | "How to use this guide": colour legend |
| `toc_page()` | table of contents (filled automatically by `build_pdf`) |
| `chapter(num, title, subtitle)` | coloured chapter banner on a new page (TOC level 0) |
| `section(title, toc=True, need=4*cm)` | heading (TOC level 1); `toc=False` before the first chapter; `need=12*cm` when a figure follows, so the heading is not orphaned |
| `subsection(title)` | smaller heading, not in TOC |
| `block_banner(n)` | navy "BLOCK n" banner (used by explain_block) |
| `python_chapter(feature_ids, num=1, uses={fid: "where in this program"})` | the auto "Python from Zero" chapter from `python_catalog.py` |
| `build_pdf(story, out_path)` | builds with a 2-pass TOC |

## Content blocks
| function | purpose |
|---|---|
| `para(text, style="body")` | paragraph (styles: body, bodyL, small) |
| `bullets(list_of_text)` | bullet list |
| `box(kind, text_or_list, title=None)` | kinds: `idea` (green, why), `model` (purple, link to equations), `what` (orange, effect of changing), `py` (teal, Python), `warn` (red, mistakes), `res` (blue, reading a result), `try` (pink, exercise), `note` (grey) |
| `one_liner(text)` | yellow "In one sentence" strip |
| `table(rows, col_widths=None, header_color=None, font_size=8.5)` | rows[0] = header; cells use markup |
| `figure(path, width_frac=1.0, caption=None)` | image + caption kept together; missing file -> red warning box |
| `side_by_side(left_flowables, right_flowables, left_frac=0.45)` | two columns (e.g. small image + text) - pass `[image(path, 0.4)]` for the image |
| `eq_box([tex, ...], label="(3.1)")` | numbered equations; matplotlib mathtext: no `\begin{cases}`, `\bmod`, `\text`, `\Big`/`\bigg` (use `\left( ... \right)`), `\dot{x}` works (use `\mathrm{...}` with `\ ` for spaces) |
| `crossing(x, y, target, log=True)` | x where a curve crosses target (e.g. SNR at BER 1e-3) |
| `sci(v)` | 1.2x10^-3 formatting |
| `PAGE_W`, `cm` | usable width and unit for column widths |

## Diagrams (diagram_kit)
- `pipeline(rows, out, snake=True)`: rows = `[(band_title, [(label, function_name), ...]), ...]` - the system's block
  diagram with the function that implements each stage. Keep labels short (2-3 words, `\n` allowed), max ~6 stages per row.
- `loop_flow(steps, out, back=(i_from, i_to), back_label="NO -> repeat")`: the simulation loop.
- `boxes_row([(heading, body), ...], out)`: concept cards (e.g. P / I / D actions).
For anything else draw with matplotlib and save PNGs at dpi=200 into `build/diag/`.

## Python catalog
`scripts/python_catalog.py` holds beginner lessons keyed by feature id (detected by `code_parser.py`).
If the program uses something not in the catalog (e.g. `asyncio`, `torch`, `simpy`), add a short lesson
in the guide yourself with `section` + `para` + `snippet` + `box("py", ...)`.
