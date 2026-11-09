"""Prepare presentation figures from the repository's AdvNet paper.

Run from any directory with Python, PyMuPDF, Pillow, NumPy, and Matplotlib.
The deck itself can be compiled without running this script.
"""

from pathlib import Path
import io
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import pymupdf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "slides" / "figures"
OUT.mkdir(exist_ok=True)
PAPER = ROOT / "docs" / "AdvNet - Revealing Performance Issues in Network Protocols by Generating Adversarial Environments.pdf"
doc = pymupdf.open(PAPER)


def embedded(page, index=0):
    xref = doc[page].get_images()[index][0]
    return Image.open(io.BytesIO(doc.extract_image(xref)["image"])).convert("RGB")


def crop_pdf(page, rect, filename):
    clip = pymupdf.Rect(rect)
    output = pymupdf.open()
    target = output.new_page(width=clip.width, height=clip.height)
    target.show_pdf_page(target.rect, doc, page, clip=clip)
    output.save(OUT / filename, garbage=4, deflate=True)


# PDF page indices are zero-based; paper figure numbers are used in filenames.
embedded(11).save(OUT / "fig02_budget.png")
embedded(14).crop((0, 0, 3600, 720)).save(OUT / "fig06_throughput.png")
crop_pdf(15, (300.0, 273.0, 427.0, 360.0), "fig07_dchannel.pdf")
crop_pdf(15, (296.0, 490.0, 440.0, 552.0), "fig08_mptcp.pdf")
crop_pdf(21, (245.0, 82.0, 437.0, 198.0), "fig11_selection.pdf")

# Digitize the plotted marker centers in Fig. 3a. Coordinates refer to the
# original 1000 x 600 embedded image, not the lower-resolution Markdown parse.
im3a = np.asarray(embedded(12, 0)).astype(float)
colors = {"GA": (31, 119, 180), "RG": (255, 127, 14),
          "GA + PLS": (44, 160, 44), "RG + PLS": (214, 39, 40)}
series = {}
for name, rgb in colors.items():
    values = []
    for x in (189, 534, 879):
        strip = im3a[20:530, x - 4:x + 5]
        distance = np.linalg.norm(strip - rgb, axis=2)
        hits = np.where(distance < 25)[0]
        # Ignore the legend in the upper-right corner.
        if x == 879:
            hits = hits[hits + 20 > 185]
        y = float(np.median(hits)) + 20
        values.append(round(0.60 - (y - 39.0) * 0.25 / (485.0 - 39.0), 4))
    series[name] = values

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 20,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.labelsize": 20, "xtick.labelsize": 20,
                     "ytick.labelsize": 20, "legend.fontsize": 19,
                     "pdf.fonttype": 42})
blue, teal, orange, gray = "#244A73", "#176B63", "#B65A2A", "#626B73"
fig, axes = plt.subplots(1, 2, figsize=(12.3, 4.15))
fig.subplots_adjust(left=.075, right=.985, bottom=.20, top=.76, wspace=.28)
styles = [(blue, "o", "-"), (orange, "s", "--"),
          (teal, "^", "-"), (gray, "D", "--")]
for (name, values), (color, marker, ls) in zip(series.items(), styles):
    axes[0].plot([0, .5, 1], values, color=color, marker=marker,
                 ls=ls, linewidth=2.3, markersize=7, label=name)
axes[0].set(ylim=(.30, .63), xticks=[0, .5, 1], yticks=[.3, .4, .5, .6],
            xlabel="Throughput weight", ylabel="Mean score")
axes[0].legend(loc="lower left", bbox_to_anchor=(-.15, 1.02), ncol=2,
               frameon=False, columnspacing=.8, handlelength=1.4)
for name, values, color, marker in [("GA", [.58, .62], blue, "o"),
                                    ("BO", [.57, .59], orange, "s"),
                                    ("EPS", [.60, .55], teal, "^")]:
    axes[1].plot([.5, 1], values, color=color, marker=marker,
                 linewidth=2.3, markersize=7, label=name)
axes[1].set(ylim=(.54, .64), xticks=[.5, 1], yticks=[.54, .58, .62],
            xlabel="Throughput weight")
axes[1].legend(loc="lower left", bbox_to_anchor=(-.07, 1.08), ncol=3,
               frameon=False, columnspacing=.8, handlelength=1.3)
for ax in axes:
    ax.grid(axis="y", color="#DADFE3", linewidth=.7)
    ax.set_axisbelow(True)
fig.savefig(OUT / "fig03_search_redrawn.pdf")
plt.close(fig)
(OUT / "fig03_plotted_values.json").write_text(json.dumps({
    "source": "Fig. 3a: digitized marker centers; Fig. 3b: plotted values",
    "fig3a": series,
    "fig3b": {"GA": [.58, .62], "BO": [.57, .59], "EPS": [.60, .55]}
}, indent=2) + "\n")

# Preserve all 17 x 17 cell colors directly from the PDF's vector rectangles.
# The overview omits cell numbers and individual labels; the following slide
# enlarges the BBR/CUBIC entries and prints their original numerical scores.
drawings = doc[13].get_drawings()
matrices = []
for x0, y0 in [(83.0448, 107.8792), (288.1056, 107.1617)]:
    matrix = np.ones((17, 17, 3))
    for row in range(17):
        for col in range(17):
            center = pymupdf.Point(x0 + (col + .5) * 8.60976,
                                   y0 + (row + .5) * 8.37060)
            matches = [d for d in drawings if d["fill"] is not None
                       and d["rect"].contains(center)
                       and 8 < d["rect"].height < 9]
            if not matches:
                raise ValueError(f"Missing heatmap cell: {x0}, {row}, {col}")
            matrix[row, col] = matches[-1]["fill"]
    matrices.append(matrix)

fig, axes = plt.subplots(1, 2, figsize=(12.3, 3.95))
fig.subplots_adjust(left=.06, right=.98, bottom=.08, top=.85, wspace=.22)
for ax, matrix, title in zip(axes, matrices,
                            ["50% throughput + 50% delay", "Throughput only"]):
    ax.imshow(matrix, interpolation="none")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=22, pad=12)
    ax.set_xlabel("Target protocol", labelpad=9)
    ax.set_ylabel("Reference protocol", labelpad=9)
    ax.add_patch(plt.Rectangle((-.5, -.5), 2, 2, fill=False,
                              ec=blue, lw=2.4, clip_on=False))
    ax.spines[["left", "bottom"]].set_visible(False)
fig.savefig(OUT / "fig04_overview.pdf")
plt.close(fig)

print("Prepared original figures and two redrawn comparisons in slides/figures/.")
