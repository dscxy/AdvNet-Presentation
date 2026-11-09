LATEX ?= pdflatex
SOURCES := presentation.tex $(wildcard sections/*.tex) $(wildcard figures/*.pdf) $(wildcard figures/*.png)

.PHONY: all
all: presentation.pdf

presentation.pdf: $(SOURCES)
	$(LATEX) -interaction=nonstopmode -halt-on-error -file-line-error presentation.tex
	$(LATEX) -interaction=nonstopmode -halt-on-error -file-line-error presentation.tex
