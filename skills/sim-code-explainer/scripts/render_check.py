#!/usr/bin/env python3
"""Visual QA of a built guide: render pages to PNG and tile them into contact sheets you can look at.

    python render_check.py Guide.pdf --out qa            # all pages, 12 per sheet (low resolution)
    python render_check.py Guide.pdf --out qa --pages 5 9 23 --dpi 80   # selected pages, readable

Needs pdftoppm (poppler-utils); falls back to pypdfium2 if available.
Look for: overlapping text, text running outside boxes, empty half pages before big figures,
missing figures (red 'Figure not found' boxes), unreadable equations, wrong chapter in the header.
"""
import argparse
import glob
import os
import shutil
import subprocess


def render(pdf, out, dpi, pages):
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, "p-*.png")):
        os.remove(f)
    if shutil.which("pdftoppm"):
        if pages:
            for p in pages:
                subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", str(p), "-l", str(p), pdf,
                                os.path.join(out, "p")], check=True)
        else:
            subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf, os.path.join(out, "p")], check=True)
    else:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(pdf)
        for i in (pages or range(1, len(doc) + 1)):
            doc[i - 1].render(scale=dpi / 72).to_pil().save(os.path.join(out, f"p-{i:03d}.png"))
    return sorted(glob.glob(os.path.join(out, "p-*.png")))


def sheets(files, out, per=12, cols=6):
    from PIL import Image
    made = []
    for s in range(0, len(files), per):
        ims = [Image.open(f).convert("RGB") for f in files[s:s + per]]
        w, h = ims[0].size
        rows = (len(ims) + cols - 1) // cols
        c = min(cols, len(ims))
        sheet = Image.new("RGB", (w * c, h * rows), "white")
        for i, im in enumerate(ims):
            sheet.paste(im.resize((w, h)), ((i % c) * w, (i // c) * h))
        p = os.path.join(out, f"sheet_{s // per + 1:02d}.png")
        sheet.save(p)
        made.append(p)
    return made


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", default="qa")
    ap.add_argument("--dpi", type=int, default=45)
    ap.add_argument("--pages", type=int, nargs="*")
    ap.add_argument("--per", type=int, default=12)
    a = ap.parse_args()
    if not os.path.exists(a.pdf):
        raise SystemExit(f"{a.pdf} does not exist - did the guide build fail? Fix the error shown by make_guide.py first.")
    files = render(a.pdf, a.out, a.dpi, a.pages)
    if a.pages:
        made = sheets(files, a.out, per=4, cols=2)
    else:
        made = sheets(files, a.out, per=a.per)
    print(f"{len(files)} pages rendered; contact sheets:")
    for m in made:
        print("  ", m)
