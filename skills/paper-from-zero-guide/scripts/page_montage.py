"""Render a PDF to page images and build montages for the visual check (Step 6).

    python3 page_montage.py guide.pdf                 # all pages at 45 dpi, 7 per row -> guide_pages.png
    python3 page_montage.py guide.pdf --dpi 75 --cols 4 --first 11 --last 14 --out eq_pages.png

Needs `pdftoppm` (poppler-utils) and Pillow.
"""
import argparse
import glob
import os
import subprocess
import tempfile
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--dpi", type=int, default=45)
    ap.add_argument("--cols", type=int, default=7)
    ap.add_argument("--first", type=int)
    ap.add_argument("--last", type=int)
    ap.add_argument("--out")
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.pdf)[0] + "_pages.png"
    with tempfile.TemporaryDirectory() as d:
        cmd = ["pdftoppm", "-r", str(a.dpi), "-png"]
        if a.first:
            cmd += ["-f", str(a.first)]
        if a.last:
            cmd += ["-l", str(a.last)]
        subprocess.run(cmd + [a.pdf, os.path.join(d, "p")], check=True)
        ims = [Image.open(f) for f in sorted(glob.glob(os.path.join(d, "p-*.png")))]
        w = max(i.width for i in ims)
        h = max(i.height for i in ims)
        rows = (len(ims) + a.cols - 1) // a.cols
        m = Image.new("RGB", (w * min(a.cols, len(ims)), h * rows), "white")
        for i, im in enumerate(ims):
            m.paste(im, ((i % a.cols) * w, (i // a.cols) * h))
        m.save(out)
    print(f"{len(ims)} pages -> {out}")


if __name__ == "__main__":
    main()
