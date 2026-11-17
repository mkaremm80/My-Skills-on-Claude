"""Concept diagrams for guides, drawn with matplotlib (no external tools).

    from diagram_kit import pipeline, loop_flow, boxes_row
    pipeline([("TRANSMITTER", [("Bits", "rng.integers"), ("QAM", "qam_mod"), ...]),
              ("CHANNEL",     [("Multipath + noise", "apply_channel")]),
              ("RECEIVER",    [("FFT", "ofdm_demodulate"), ...])],
             "build/diag/pipeline.png", snake=True)
    loop_flow(["for each SNR", "draw random input", "run the system", "count errors",
               "enough samples?", "store result"], back=(4, 1), back_label="NO -> repeat",
              out="build/diag/loop.png")

Each stage = (label, function_name_or_empty). Colours rotate automatically.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

PALETTE = ["#455a64", "#1565c0", "#00897b", "#6a1b9a", "#8e24aa", "#ef6c00", "#c62828", "#2e7d32",
           "#0277bd", "#ad1457"]
BAND = [("#e3f2fd", "#90caf9", "#0d47a1"), ("#fff3e0", "#ffcc80", "#e65100"), ("#e8f5e9", "#a5d6a7", "#1b5e20"),
        ("#f3e5f5", "#ce93d8", "#4a148c"), ("#e0f2f1", "#80cbc4", "#004d40")]


def _wrap_label(text, w, fs):
    """Wrap a label so it fits a box w data-units (inches) wide at font size fs."""
    import textwrap
    width = max(6, int(w * 120 / fs))           # ~ characters per line
    return "\n".join(textwrap.fill(part, width) for part in text.split("\n"))


def _box(ax, x, y, w, h, text, fc, sub=None, fs=9):
    text = _wrap_label(text, w, fs)
    while text.count("\n") >= 3 and fs > 6:     # too many lines -> smaller font
        fs -= 0.6
        text = _wrap_label(text.replace("\n", " "), w, fs)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec="none"))
    ax.text(x + w / 2, y + h / 2 + (0.1 if sub else 0), text, ha="center", va="center", fontsize=fs,
            color="white", weight="bold", wrap=True)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.2, sub, ha="center", va="center", fontsize=6.6, color="white",
                family="monospace")


def _arrow(ax, p0, p1, col="#37474f", rad=0.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=12, color=col, lw=1.6,
                                 connectionstyle=f"arc3,rad={rad}"))


def pipeline(rows, out, snake=True, width=12):
    """rows: [(band_title, [(label, func), ...]), ...] drawn as horizontal bands top to bottom.
    snake=True: odd rows run right-to-left so the flow reads like a U (Tx -> channel -> Rx)."""
    n_rows = len(rows)
    row_h = 1.9
    H = n_rows * row_h + 0.2
    fig, ax = plt.subplots(figsize=(width, H * 0.95))
    ax.set_xlim(0, width); ax.set_ylim(0, H); ax.axis("off")
    k = 0
    prev_last = None
    for r, (title, stages) in enumerate(rows):
        y0 = H - (r + 1) * row_h
        bg, ec, tc = BAND[r % len(BAND)]
        ax.add_patch(Rectangle((0.1, y0 + 0.1), width - 0.2, row_h - 0.15, fc=bg, ec=ec, lw=1))
        ax.text(0.25, y0 + row_h - 0.28, title, fontsize=9, color=tc, weight="bold")
        n = len(stages)
        gap = 0.35
        w = min(2.2, (width - 0.6 - gap * (n - 1)) / n)
        total = n * w + (n - 1) * gap
        x_start = (width - total) / 2
        xs = [x_start + i * (w + gap) for i in range(n)]
        if snake and r % 2 == 1:
            xs = xs[::-1]
        yb = y0 + 0.3
        for i, (label, func) in enumerate(stages):
            _box(ax, xs[i], yb, w, 1.05, label, PALETTE[k % len(PALETTE)], sub=(func + "()") if func else None,
                 fs=8.6 if len(label) < 22 else 7.6)
            k += 1
            if i > 0:
                if xs[i] > xs[i - 1]:
                    _arrow(ax, (xs[i - 1] + w, yb + 0.52), (xs[i], yb + 0.52))
                else:
                    _arrow(ax, (xs[i - 1], yb + 0.52), (xs[i] + w, yb + 0.52))
        first, last = (xs[0], yb + 1.05), (xs[-1], yb)
        if prev_last is not None:
            _arrow(ax, (prev_last[0] + w / 2, prev_last[1]), (first[0] + w / 2, first[1]), col="#e65100")
        prev_last = (xs[-1], yb)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def loop_flow(steps, out, back=None, back_label="", width=12):
    """A left-to-right flowchart. back=(from_index, to_index) draws a return arrow below the boxes."""
    n = len(steps)
    fig, ax = plt.subplots(figsize=(width, 2.6))
    ax.set_xlim(0, width); ax.set_ylim(0, 2.6); ax.axis("off")
    w = (width - 0.2 - 0.3 * (n - 1)) / n
    xs = [0.1 + i * (w + 0.3) for i in range(n)]
    for i, s in enumerate(steps):
        _box(ax, xs[i], 1.0, w, 1.0, s, PALETTE[i % len(PALETTE)], fs=7.6)
        if i:
            _arrow(ax, (xs[i - 1] + w, 1.5), (xs[i], 1.5))
    if back:
        a, b = back
        ax.annotate("", xy=(xs[b] + w / 2, 1.0), xytext=(xs[a] + w / 2, 1.0),
                    arrowprops=dict(arrowstyle="-|>", color="#c62828", lw=1.5, connectionstyle="arc3,rad=-0.35"))
        ax.text((xs[a] + xs[b]) / 2 + w / 2, 0.1, back_label, ha="center", color="#c62828", fontsize=8.5)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out


def boxes_row(items, out, title=None, width=11):
    """A row of coloured concept cards: items = [(heading, body_text), ...]."""
    n = len(items)
    fig, ax = plt.subplots(figsize=(width, 2.4))
    ax.set_xlim(0, width); ax.set_ylim(0, 2.4); ax.axis("off")
    w = (width - 0.2 - 0.25 * (n - 1)) / n
    for i, (h, body) in enumerate(items):
        x = 0.1 + i * (w + 0.25)
        col = PALETTE[(i + 1) % len(PALETTE)]
        ax.add_patch(FancyBboxPatch((x, 0.1), w, 2.0, boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc="white", ec=col, lw=2))
        ax.add_patch(FancyBboxPatch((x, 1.6), w, 0.5, boxstyle="round,pad=0.02,rounding_size=0.08", fc=col, ec=col))
        ax.text(x + w / 2, 1.85, h, ha="center", va="center", color="white", weight="bold", fontsize=9)
        ax.text(x + w / 2, 0.85, body, ha="center", va="center", fontsize=8, wrap=True)
    if title:
        ax.set_title(title, fontsize=10)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out
