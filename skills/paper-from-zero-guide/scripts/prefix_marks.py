"""Make annotate-equations mark names unique.

Inside the k-th `eqbox` environment, every mark name used by \\eqnmarkbox / \\eqnmark /
\\annotate gets the prefix "q<k>" (q1, q2, ...). Write plain names (e.g. "mu", "y")
in each box, then run:

    python3 prefix_marks.py guide.tex            # edits the file in place
    python3 prefix_marks.py guide.tex out.tex    # writes a new file

Names that already start with "q<digits>" are left alone, so running twice is safe.
"""
import re
import sys

BOX = re.compile(r"(\\begin\{eqbox\}.*?\\end\{eqbox\})", re.S)
MARK = re.compile(r"(\\eqnmark(?:box)?(?:\[[^\]]*\])?\{)([A-Za-z0-9]+)(\})")
ANNO = re.compile(r"(\\annotate(?:\[[^\]]*\])?\{[^}]*\}\{)([A-Za-z0-9,]+)(\})")


def fix_box(text, k):
    pre = f"q{k}"

    def one(name):
        return name if re.match(r"q\d+", name) else pre + name

    text = MARK.sub(lambda m: m.group(1) + one(m.group(2)) + m.group(3), text)
    text = ANNO.sub(lambda m: m.group(1) + ",".join(one(n) for n in m.group(2).split(",")) + m.group(3), text)
    return text


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    s = open(src, encoding="utf-8").read()
    parts = BOX.split(s)
    k = 0
    for i, p in enumerate(parts):
        if p.startswith("\\begin{eqbox}"):
            k += 1
            parts[i] = fix_box(p, k)
    open(dst, "w", encoding="utf-8").write("".join(parts))
    print(f"prefixed marks in {k} eqbox blocks -> {dst}")


if __name__ == "__main__":
    main()
