#!/usr/bin/env python3
"""Turn a block-marked Python program into a Google Colab notebook (one markdown title + one code cell per block).

    python make_notebook.py my_sim.py my_sim.ipynb [--title "My simulator"] [--pip "simpy pandas"]

* Markers:  # ==== [BLOCK n] Title ====  (add them with code_parser.py --write-markers).
* Blocks nested inside a function (indented markers) stay in the cell of the enclosing block.
* An  if __name__ == "__main__":  block is unwrapped so its statements run directly in a cell.
* --pip adds a first cell that installs packages Colab does not have.
"""
import argparse
import re
import textwrap
import json

MARK = re.compile(r"^#\s*=+\s*\[BLOCK\s+(\d+)\]\s*(.+?)\s*=*\s*$")


def cell(kind, src):
    c = {"cell_type": kind, "metadata": {}, "source": src}
    if kind == "code":
        c.update(execution_count=None, outputs=[])
    return c


def unwrap_main(body):
    lines = body.split("\n")
    for i, l in enumerate(lines):
        if re.match(r'^if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', l):
            inner = textwrap.dedent("\n".join(lines[i + 1:]))
            return "\n".join(lines[:i] + [inner]).strip()
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--title", default=None)
    ap.add_argument("--pip", default="")
    a = ap.parse_args()
    src = open(a.src, encoding="utf-8").read().split("\n")
    marks = [(i, m.group(1), m.group(2)) for i, l in enumerate(src) for m in [MARK.match(l)] if m]  # top level only
    cells = [cell("markdown", f"# {a.title or a.src}\n\nRun everything with **Runtime → Run all**. "
                              "Each block below is explained in the companion PDF guide (same block numbers).")]
    if a.pip:
        cells.append(cell("code", f"!pip install -q {a.pip}"))
    if not marks:
        cells.append(cell("code", unwrap_main("\n".join(src))))
    else:
        if marks[0][0] > 0 and "\n".join(src[:marks[0][0]]).strip():
            cells.append(cell("code", "\n".join(src[:marks[0][0]]).strip()))
        for k, (i, n, title) in enumerate(marks):
            j = marks[k + 1][0] if k + 1 < len(marks) else len(src)
            body = "\n".join(src[i:j]).rstrip()
            cells.append(cell("markdown", f"## Block {n}: {title}"))
            cells.append(cell("code", unwrap_main(body)))
    nb = {"cells": cells, "metadata": {"colab": {"provenance": []},
                                       "kernelspec": {"name": "python3", "display_name": "Python 3"},
                                       "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 5}
    for c in nb["cells"]:                      # nbformat wants a list of lines
        c["source"] = [ln + "\n" for ln in c["source"].split("\n")]
        c["source"][-1] = c["source"][-1].rstrip("\n")
    json.dump(nb, open(a.out, "w"), indent=1)
    print(f"wrote {a.out}: {len(cells)} cells")


if __name__ == "__main__":
    main()
