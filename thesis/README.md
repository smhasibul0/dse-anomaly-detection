# Thesis (Uttara University template)

The thesis book, built on the Uttara University CSE thesis LaTeX template v1.0
(class `classes/uuthesis.cls`, by Dr. S M Nazmus Sadat). The untouched template is kept
in the project's shared files under `thesis/template-original/`.

## Build

Overleaf: upload this folder as a zip and set `main.tex` as the main document
(compiler pdfLaTeX).

Locally (TeX Live with `latexmk`):

```bash
cd thesis
latexmk -pdf main.tex
```

`latexmk -C` cleans the build files. On Debian or Ubuntu the packages needed are
`texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-science latexmk`.

## What to edit

| What | Where |
|---|---|
| Title, student names and IDs, supervisor, committee, dates | `frontmatters/metadata.tex` (every front-matter page reads from it) |
| Abstract, dedication, acknowledgment | `frontmatters/` |
| Symbols and abbreviations | `frontmatters/symbol.tex`, `frontmatters/abbreviation.tex` |
| Chapters | `chapter1/` to `chapter5/`, figures in each chapter's `figures/` |
| References | `backmatters/references.bib` |
| Appendices | `backmatters/appendix.tex`, page numbers typed by hand in `backmatters/listofappendices.tex` |

Unwritten text is marked `\todo{...}` and shows in the PDF as *[TODO: ...]*. Search for
`\todo` and `[` placeholders before submission.

## Format fixed by the template (do not change)

- A4, 12 pt, Times, margins 3 cm left, right and top; single spacing.
- Front matter order, roman page numbers: title page, second title page, abstract,
  clearance page, submission (declaration) page, copyright declaration, dedication,
  acknowledgment, table of contents, list of tables, list of figures, symbols,
  abbreviations, list of appendices.
- Five chapters, arabic page numbers: Introduction, Literature Review, Methodology,
  Results and Analysis, Conclusion. Then References and Appendices A and B.
- Citations: numeric IEEE style (`IEEEtran`), via BibTeX.
- Figures, tables and equations are numbered by chapter.

The template states no page or word limit.

## Changes from the original template

- `main.tex`: the appendix was included from `chapters/appendix`, which does not exist,
  so the template did not compile. It now points to `backmatters/appendix`.
- `main.tex`: loads `frontmatters/metadata.tex` so names and dates are set once.
- Front matter pages use the metadata macros instead of the sample names; no layout change.
- Chapter files hold this project's section outline instead of the sample content.

## How the research plan maps onto the chapters

| Plan section | Thesis chapter |
|---|---|
| Introduction | Chapter 1, Introduction |
| Related Work | Chapter 2, Literature Review |
| Data and Labeling, Method | Chapter 3, Methodology |
| Experiments, Results and Discussion | Chapter 4, Results and Analysis |
| Limitations, Conclusion | Chapter 5, Conclusion |

## References

`backmatters/references.bib` holds the 23 papers from the project's literature table.
Entries with `and others` were "et al." in the table and need full author lists; DOIs
still need a click-check; page numbers are missing for most entries.
