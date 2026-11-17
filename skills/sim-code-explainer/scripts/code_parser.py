#!/usr/bin/env python3
"""Analyse a Python program for the guide.

    python code_parser.py my_sim.py                      # report -> my_sim.analysis.json + summary on screen
    python code_parser.py my_sim.py --write-markers out.py   # copy of the code with  # ==== [BLOCK n] ... ====
                                                         # markers inserted (logic untouched)

Reports: blocks (existing or proposed), functions/classes with line ranges and docstrings, imports,
tunable parameters (top-level constants, dict(...) / {...} config entries, function defaults),
Python features used (ids of python_catalog.py) with the lines where they appear, figures saved, etc.
"""
import ast
import json
import re
import sys
import argparse

MARK = re.compile(r"#\s*=+\s*\[BLOCK\s+(\d+)\]\s*(.+?)\s*=*\s*$")


def first_doc_line(node):
    d = ast.get_docstring(node)
    return d.strip().split("\n")[0].strip().rstrip(".") if d else ""


def node_start(node):
    starts = [node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])]
    return min(starts)


def literal(node):
    try:
        v = ast.literal_eval(node)
        return v if isinstance(v, (int, float, complex, str, bool, tuple, list)) else None
    except Exception:
        return None


def analyse(path):
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")
    tree = ast.parse(text)
    rep = dict(file=path, n_lines=len(lines), functions=[], classes=[], imports=[], parameters=[],
               features={}, figures_saved=[], has_main_guard=False, uses_random_seed=False)

    # ---------- existing markers
    marks = [(i + 1, int(m.group(1)), m.group(2)) for i, l in enumerate(lines) for m in [MARK.search(l)] if m]
    rep["has_markers"] = bool(marks)
    rep["blocks"] = []
    for k, (ln, n, title) in enumerate(marks):
        end = marks[k + 1][0] - 1 if k + 1 < len(marks) else len(lines)
        while end > ln and not lines[end - 1].strip():
            end -= 1
        rep["blocks"].append(dict(n=n, title=title, start=ln, end=end))

    def feat(fid, node):
        rep["features"].setdefault(fid, [])
        ln = getattr(node, "lineno", None)
        if ln and len(rep["features"][fid]) < 6 and ln not in rep["features"][fid]:
            rep["features"][fid].append(ln)

    rep["features"]["basics"] = [1]
    for node in ast.walk(tree):
        t = type(node)
        if t in (ast.Import, ast.ImportFrom):
            mod = node.module if t is ast.ImportFrom else None
            names = [a.name for a in node.names]
            rep["imports"].append(dict(line=node.lineno, module=mod or names[0], names=names))
            feat("imports", node)
            full = " ".join([mod or ""] + names)
            for key, fid in [("numpy", "numpy"), ("pandas", "pandas"), ("scipy", "scipy"),
                             ("matplotlib", "matplotlib"), ("random", "random"), ("dataclass", "dataclasses")]:
                if key in full:
                    feat(fid, node)
        elif t is ast.FunctionDef or t is ast.AsyncFunctionDef:
            feat("functions", node)
            a = node.args
            if a.kwarg or a.vararg:
                feat("kwargs", node)
            if any(x.annotation for x in a.args) or node.returns:
                feat("typing", node)
            defaults = a.defaults
            pos = a.args[len(a.args) - len(defaults):]
            for arg, d in zip(pos, defaults):
                v = literal(d)
                if v is not None:
                    rep["parameters"].append(dict(name=arg.arg, value=repr(v), line=node.lineno,
                                                  scope=f"default of {node.name}()"))
            if any(isinstance(n, (ast.FunctionDef,)) for n in node.body):
                feat("functions", node)
            rep["functions"].append(dict(name=node.name, start=node_start(node), end=node.end_lineno,
                                         args=[x.arg for x in a.args], doc=first_doc_line(node)))
        elif t is ast.ClassDef:
            feat("classes", node)
            if any("dataclass" in ast.unparse(d) for d in node.decorator_list):
                feat("dataclasses", node)
            rep["classes"].append(dict(name=node.name, start=node_start(node), end=node.end_lineno,
                                       doc=first_doc_line(node),
                                       methods=[m.name for m in node.body if isinstance(m, ast.FunctionDef)]))
        elif t is ast.JoinedStr:
            feat("strings", node)
        elif t in (ast.List, ast.Tuple):
            feat("containers", node)
        elif t is ast.Subscript and isinstance(node.slice, ast.Slice):
            feat("containers", node)
        elif t is ast.Dict:
            feat("dicts", node)
        elif t in (ast.If, ast.For, ast.While):
            feat("control", node)
            if t is ast.If and "__name__" in ast.unparse(node.test):
                feat("main_guard", node)
                rep["has_main_guard"] = True
        elif t in (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp):
            feat("comprehensions", node)
        elif t is ast.Lambda:
            feat("lambda", node)
        elif t in (ast.Try, ast.Raise):
            feat("exceptions", node)
        elif t is ast.With:
            feat("with_files", node)
        elif t in (ast.Yield, ast.YieldFrom):
            feat("generators", node)
        elif t is ast.Assert:
            feat("assert", node)
        elif t is ast.BinOp:
            if isinstance(node.op, ast.MatMult):
                feat("numpy_linalg", node)
            if isinstance(node.op, (ast.BitXor, ast.LShift, ast.RShift, ast.BitAnd, ast.BitOr)):
                feat("bitwise", node)
        elif t is ast.Constant and isinstance(node.value, complex):
            feat("complex", node)
        elif t is ast.Attribute:
            if node.attr == "linalg":
                feat("numpy_linalg", node)
            elif node.attr == "fft":
                feat("numpy_fft", node)
            elif node.attr in ("default_rng", "random", "randn", "rand", "normal", "seed"):
                feat("random", node)
        elif t is ast.Call:
            fn = ast.unparse(node.func)
            if fn in ("enumerate", "zip"):
                feat("enumerate_zip", node)
            if fn == "dict":
                feat("dicts", node)
                for kw in node.keywords:       # dict(A=1, B=2) configuration entries
                    v = literal(kw.value)
                    if kw.arg and v is not None:
                        rep["parameters"].append(dict(name=kw.arg, value=repr(v), line=kw.value.lineno,
                                                      scope="dict(...) entry"))
            if any(k.arg is None for k in node.keywords):
                feat("kwargs", node)
            if fn.endswith("savefig") and node.args:
                rep["figures_saved"].append(ast.unparse(node.args[0]))
            if "seed" in ast.unparse(node) or fn.endswith("default_rng"):
                rep["uses_random_seed"] = True
        elif t is ast.Subscript:
            if "None" in ast.unparse(node.slice):
                feat("numpy_broadcast", node)
            feat("containers", node)

    # ---------- top-level constants (simple parameters)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            v = literal(node.value)
            if v is not None and (not isinstance(v, (list, tuple)) or len(v) < 8):
                if True:
                    rep["parameters"].append(dict(name=node.targets[0].id, value=repr(v), line=node.lineno,
                                                  scope="top-level"))
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for k, val in zip(node.value.keys, node.value.values):
                kv, vv = literal(k) if k else None, literal(val)
                if isinstance(kv, str) and vv is not None:
                    rep["parameters"].append(dict(name=kv, value=repr(vv), line=val.lineno, scope="{...} entry"))

    # ---------- proposed blocks (only when the file has no markers)
    if not marks:
        rep["proposed_blocks"] = propose_blocks(tree, lines)
    rep["long_blocks"] = [b for b in (rep["blocks"] or rep.get("proposed_blocks", []))
                          if b["end"] - b["start"] > 70]
    rep["parameters"].sort(key=lambda p: p["line"])
    rep["feature_ids"] = list(rep["features"])
    return rep


def propose_blocks(tree, lines):
    """Group top-level statements: settings/imports, one block per def/class, script parts, main."""
    groups = []
    cur = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if cur:
                groups.append(cur)
                cur = None
            kind = "class" if isinstance(node, ast.ClassDef) else "def"
            doc = first_doc_line(node)
            title = (f"class {node.name}" if kind == "class" else f"{node.name}()") + (f": {doc}" if doc else "")
            groups.append(dict(title=title[:90], start=node_start(node), end=node.end_lineno))
        elif isinstance(node, ast.If) and "__name__" in ast.unparse(node.test):
            if cur:
                groups.append(cur)
                cur = None
            groups.append(dict(title="Main program", start=node.lineno, end=node.end_lineno))
        else:
            is_setup = isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign, ast.Expr))
            label = "Imports and settings" if (not groups and is_setup) else "Script part"
            if cur is None:
                cur = dict(title=label, start=node.lineno, end=node.end_lineno)
            else:
                cur["end"] = node.end_lineno
    if cur:
        groups.append(cur)
    # pull comment lines directly above a block into it
    for g in groups:
        s = g["start"]
        while s > 1 and lines[s - 2].strip().startswith("#"):
            s -= 1
        g["start"] = s
    for i, g in enumerate(groups):
        g["n"] = i
    return groups


def write_markers(path, rep, out):
    lines = open(path, encoding="utf-8").read().split("\n")
    blocks = rep.get("proposed_blocks") or []
    if not blocks:
        print("file already has markers or nothing to mark; copying unchanged")
    inserts = {b["start"]: f"# ==== [BLOCK {b['n']}] {b['title']} ====" for b in blocks}
    new = []
    for i, ln in enumerate(lines, start=1):
        if i in inserts:
            if new and new[-1].strip():
                new.append("")
            new.append(inserts[i])
        new.append(ln)
    open(out, "w", encoding="utf-8").write("\n".join(new))
    print(f"wrote {out} with {len(blocks)} block markers (edit the titles freely; never change the logic)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--write-markers", metavar="OUT")
    ap.add_argument("--json", metavar="OUT", help="analysis file (default: <src>.analysis.json)")
    a = ap.parse_args()
    rep = analyse(a.src)
    out = a.json or re.sub(r"\.py$", "", a.src) + ".analysis.json"
    json.dump(rep, open(out, "w"), indent=1, default=str)
    print(f"{a.src}: {rep['n_lines']} lines, {len(rep['functions'])} functions, {len(rep['classes'])} classes")
    print("markers present:", rep["has_markers"])
    for b in rep["blocks"] or rep.get("proposed_blocks", []):
        print(f"  BLOCK {b['n']:>2}  lines {b['start']:>4}-{b['end']:<4} {b['title']}")
    print("python features:", ", ".join(rep["feature_ids"]))
    print("tunable parameters found:", len(rep["parameters"]))
    for p in rep["parameters"][:40]:
        print(f"   line {p['line']:>4}  {p['name']} = {p['value']}   ({p['scope']})")
    if rep["long_blocks"]:
        print("NOTE: blocks longer than 70 lines (consider splitting with extra markers):",
              [b["title"] for b in rep["long_blocks"]])
    print("analysis written to", out)
    if a.write_markers:
        write_markers(a.src, rep, a.write_markers)


if __name__ == "__main__":
    main()
