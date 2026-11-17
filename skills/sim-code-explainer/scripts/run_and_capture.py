#!/usr/bin/env python3
"""Run a Python program and capture everything the guide needs.

    python run_and_capture.py my_sim.py --out run_out [--timeout 900] [--fast-env FAST=1] [-- args...]

What it does
  * runs the program in its own folder copy (run_out/work/), as __main__, with a non-interactive
    matplotlib backend, so plt.show() never blocks;
  * every figure that is "shown" (or still open at the end) and was NOT saved by the program is saved as
    run_out/figures/auto_XX.png (numbered in display order); figures the program saves itself are copied
    with their own names (sub-folders become "folder__name.png"), so nothing is duplicated;
  * stdout/stderr go to run_out/stdout.txt; a summary goes to run_out/run_report.json
    (status, seconds, figures, new files, last lines of output, the error if any).
The program's own logic is never modified.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

RUNNER = r'''
import os, sys, runpy, atexit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
_out = os.environ["SCE_FIG_DIR"]
_n = [0]
from matplotlib.figure import Figure
_orig_savefig = Figure.savefig
def _marking_savefig(self, *a, **k):
    self._sce_saved = True                 # the program saved this figure itself -> no duplicate auto_ copy
    return _orig_savefig(self, *a, **k)
Figure.savefig = _marking_savefig
def _save_all(*a, **k):
    for num in plt.get_fignums():
        fig = plt.figure(num)
        if getattr(fig, "_sce_saved", False):
            continue
        _n[0] += 1
        _orig_savefig(fig, os.path.join(_out, f"auto_{_n[0]:02d}.png"), dpi=130, bbox_inches="tight")
    plt.close("all")
plt.show = _save_all
atexit.register(_save_all)
sys.argv = [sys.argv[1]] + sys.argv[2:]
runpy.run_path(sys.argv[0], run_name="__main__")
'''


def snapshot(d):
    out = {}
    for root, _, files in os.walk(d):
        for f in files:
            p = os.path.join(root, f)
            out[os.path.relpath(p, d)] = os.path.getmtime(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default="run_out")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--env", action="append", default=[], help="extra environment variable NAME=VALUE")
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()

    src = os.path.abspath(a.src)
    out = os.path.abspath(a.out)
    work = os.path.join(out, "work")
    figs = os.path.join(out, "figures")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(figs, exist_ok=True)
    # copy the program's folder (small files only) so relative paths and data files keep working
    srcdir = os.path.dirname(src)
    skip = shutil.ignore_patterns("run_out*", "build", "*.pdf", ".git", "__pycache__", "*.zip", "node_modules",
                                  ".venv", "venv")

    def ignore(d, names):          # also skip files bigger than 200 MB
        big = {n for n in names if os.path.isfile(os.path.join(d, n))
               and os.path.getsize(os.path.join(d, n)) > 200e6}
        return set(skip(d, names)) | big
    shutil.copytree(srcdir, work, ignore=ignore, dirs_exist_ok=True)
    runner = os.path.join(out, "_runner.py")
    open(runner, "w").write(RUNNER)
    env = dict(os.environ, MPLBACKEND="Agg", SCE_FIG_DIR=figs, PYTHONUNBUFFERED="1")
    for kv in a.env:
        k, v = kv.split("=", 1)
        env[k] = v
    before = snapshot(work)
    t0 = time.time()
    status, err = "ok", ""
    with open(os.path.join(out, "stdout.txt"), "w") as log:
        try:
            p = subprocess.run([sys.executable, runner, os.path.join(work, os.path.basename(src))] + a.args,
                               cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=a.timeout)
            if p.returncode != 0:
                status = f"error (exit code {p.returncode})"
        except subprocess.TimeoutExpired:
            status = f"timeout after {a.timeout} s"
    secs = time.time() - t0
    after = snapshot(work)
    new_files = sorted(f for f in after if f not in before or after[f] > before.get(f, 0))
    for f in new_files:                                   # collect images the program saved itself
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg")):
            dst = os.path.join(figs, f.replace(os.sep, "__"))
            shutil.copy2(os.path.join(work, f), dst)
    text = open(os.path.join(out, "stdout.txt"), errors="replace").read()
    if status != "ok":
        err = "\n".join(text.strip().split("\n")[-15:])
    rep = dict(program=src, status=status, seconds=round(secs, 1), figures=sorted(os.listdir(figs)),
               new_files=new_files, stdout_tail=text.strip().split("\n")[-40:], error=err,
               work_dir=work, figures_dir=figs)
    json.dump(rep, open(os.path.join(out, "run_report.json"), "w"), indent=1)
    print(f"status: {status}   time: {secs:.1f} s")
    print(f"figures ({len(rep['figures'])}) in {figs}:")
    for f in rep["figures"]:
        print("   ", f)
    print("new files:", ", ".join(new_files[:30]))
    if err:
        print("---- error ----\n" + err)
    print("full output:", os.path.join(out, "stdout.txt"))


if __name__ == "__main__":
    main()
