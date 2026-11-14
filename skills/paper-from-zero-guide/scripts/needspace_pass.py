"""Put \\Needspace{14\\baselineskip} before every \\section (avoids orphan headings).

    python3 needspace_pass.py guide.tex      # edits in place; safe to run twice
"""
import sys

p = sys.argv[1]
lines = open(p, encoding="utf-8").read().split("\n")
out = []
for ln in lines:
    if ln.lstrip().startswith("\\section") and not (out and out[-1].strip().startswith("\\Needspace")):
        out.append("\\Needspace{14\\baselineskip}")
    out.append(ln)
s = "\n".join(out)
open(p, "w", encoding="utf-8").write(s)
print("done:", s.count("\\Needspace{"), "Needspace commands")
