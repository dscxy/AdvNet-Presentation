# AdvNet slide deck

`presentation.pdf` is the review copy: 30 static main slides and four backup
slides. Main-slide numbers match PDF page numbers. Backup slides B1–B4 occupy
PDF pages 31–34. There are no overlays or hidden clicks.

The deck follows `../scripts/presentation_script.md`. The corresponding
`../scripts/slide_cues.md` gives exact spoken cues for slide changes, a 25-minute
rehearsal schedule, and the speaker handoff. The script itself is unchanged.

## Editing and building

`presentation.tex` defines the Beamer theme and includes the editable content
under `sections/`. The layout follows the supplied `agent_memory_v5` reference:
white background, blue titles, teal emphasis, a chapter navigation bar, a
bottom-left figure note, and a bottom-right page number.

The canvas is 13.333 × 7.5 inches. Body text is normally 24 pt, secondary text
20–22 pt, and navigation and footers 18.5 pt. Diagram labels, equation indices,
and displayed paper figures are also sized for the repository's 18 pt minimum.

From this directory, run:

```sh
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error presentation.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error presentation.tex
```

Alternatively, run `make -C slides` from the repository root. A standard MiKTeX
or TeX Live installation with Beamer, Latin Modern, TikZ, booktabs, tabularx,
and colortbl is sufficient. Generated auxiliary files are ignored locally.

## Figures

All source figures come from the paper PDF already in `docs/`. The provided
teammate slides informed the content organization and GA teaching example; their
slide layouts and artwork are not copied into this deck. The GA vectors and
mutation example also appear in the accepted script.

| Asset / slide | Preparation |
| --- | --- |
| Architecture, slide 5 | New TikZ diagram based on Fig. 1. |
| Trace and comparison, slides 7–8 | New teaching diagram; bounds from Table 1 and numerical entries from Table 2. |
| `fig02_budget.png`, slide 14 | Original embedded image for Fig. 2. |
| `fig03_search_redrawn.pdf`, slide 11 | Replotted Fig. 3a–b with larger labels. Fig. 3a marker centers are digitized from the original embedded image; Fig. 3b uses its plotted values. Values are recorded in `fig03_plotted_values.json`. |
| `fig04_overview.pdf`, slide 17 | All 17 × 17 cell colors in each panel are copied directly from the PDF's vector rectangles. Individual labels and numbers are omitted in this overview. Blue boxes identify the BBR/CUBIC block. |
| BBR/CUBIC table, slide 18 | The four numerical entries from Fig. 4 are shown at full text size. |
| `fig06_throughput.png`, slide 21 | Original throughput panel from Fig. 6; the other two panels are cropped out. |
| `fig07_dchannel.pdf`, slide 27 | Original vector Fig. 7, cropped from the paper page. |
| `fig08_mptcp.pdf`, slide 28 | Original vector Fig. 8, with its two panels and original axes retained. |
| `fig11_selection.pdf`, slide B4 | Original vector Fig. 11, cropped from the paper page. |
| Other diagrams | New TikZ teaching diagrams based on the script and the paper's case descriptions; marked as presenter illustrations. |

To regenerate the included figure assets, install Python packages `pymupdf`,
`Pillow`, `numpy`, and `matplotlib`, then run:

```sh
python slides/generate_figures.py
```

The included assets are sufficient for ordinary LaTeX compilation.
