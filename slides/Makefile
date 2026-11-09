# The v3 source uses fontspec and requires XeLaTeX (or a compatible override).
# Command-line overrides remain available, e.g. make LATEX=lualatex.
LATEX = xelatex
LATEXFLAGS ?= -interaction=nonstopmode -halt-on-error -file-line-error
SOURCES := presentation.tex Makefile \
	$(wildcard notes/*.tex) \
	$(wildcard assets/*.pdf assets/*.png assets/*.jpg assets/*.jpeg)

.PHONY: all
all: presentation.pdf

presentation.pdf: $(SOURCES)
	$(LATEX) $(LATEXFLAGS) presentation.tex
	$(LATEX) $(LATEXFLAGS) presentation.tex
