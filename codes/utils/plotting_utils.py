#!/usr/bin/env python3
"""Shared plotting settings for publication-quality figures."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# Elsevier journal style
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.grid": False,
    "grid.alpha": 0.15,
    "grid.linewidth": 0.4,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.5,
    "lines.markersize": 5,
    "figure.figsize": (7.0, 4.5),
    "text.usetex": False,
})

# Color palette (colorblind-friendly, Dark2 + Set2)
COLORS = {
    "primary":   "#1b9e77",
    "secondary": "#d95f02",
    "tertiary":  "#7570b3",
    "quaternary":"#e7298a",
    "quinary":   "#66a61e",
    "senary":    "#e6ab02",
    "septenary": "#a6761d",
    "octonary":  "#666666",
}

FIGURE_DIR = None  # Set by caller

def save_figure(fig, name, formats=("pdf", "png")):
    """Save figure in multiple formats."""
    import os
    out_dir = FIGURE_DIR or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "manuscript", "figures")
    os.makedirs(out_dir, exist_ok=True)
    for fmt in formats:
        path = os.path.join(out_dir, f"{name}.{fmt}")
        fig.savefig(path, format=fmt)
        print(f"  Saved: {path}")
    plt.close(fig)
