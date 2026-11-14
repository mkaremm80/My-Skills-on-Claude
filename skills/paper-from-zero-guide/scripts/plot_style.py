"""Shared matplotlib style for the helper drawings.

Usage (from your figure script):
    import sys; sys.path.insert(0, "<skill folder>/scripts")
    from plot_style import setup, save, note, COLORS
    setup()
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    ...
    note(ax, "best port", xy=(3, 10), xytext=(5, 14))
    save(fig, "figs/f1_example")      # writes .pdf (for LaTeX) and .png at 70 dpi (for checking)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = dict(navy="#1B3A5C", teal="#00798C", rosered="#D1495B",
              amber="#E09F3E", leaf="#2E8B57", plum="#6A4C93")
ARROW = dict(arrowstyle="-|>", color="#C0392B")
NOTE_BOX = dict(boxstyle="round,pad=0.3", fc="#FFF8E1", ec="#E09F3E")


def setup():
    plt.rcParams.update({
        "font.family": "STIXGeneral", "mathtext.fontset": "stix", "pdf.fonttype": 42,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.3,
        "font.size": 10.5, "legend.fontsize": 9, "axes.titlesize": 11,
        "figure.figsize": (6.6, 3.0),
    })


def note(ax, text, xy, xytext, fontsize=9):
    """Arrow note in an empty area of the plot."""
    return ax.annotate(text, xy=xy, xytext=xytext, arrowprops=ARROW, bbox=NOTE_BOX, fontsize=fontsize)


def save(fig, path_no_ext):
    os.makedirs(os.path.dirname(path_no_ext) or ".", exist_ok=True)
    fig.tight_layout()
    fig.savefig(path_no_ext + ".pdf")
    fig.savefig(path_no_ext + ".png", dpi=70)
    plt.close(fig)
