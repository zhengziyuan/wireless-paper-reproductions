# Final IEEE Fig. 4 and three saved author-working means

This is a **conditional, read-only graphical comparison**, not a new
simulation, recovery of the author's complete plotting workflow, or a
full-paper reproduction. The source figure was inspected in the user-supplied
final IEEE paper, DOI 10.1109/JSAC.2024.3460068, Fig. 4 on printed page 291
(PDF page 13). No publisher PDF, extracted SVG, author ZIP, or figure image is
redistributed here.

The compared saved values are in `test_varsigma_316/plot_record0120.mat`,
shape 18×20×5. For its second slice and first twelve columns, this check takes
the ordinary mean of rows 1–3 for AP-AO, rows 4–6 for MR-S-PA, and rows 7–9
for MR-TTS-PA. It compares their corresponding ordinals to the 12 vertices of
each visually identified final-PDF curve, without fitting, interpolation,
rescaling of values, or reordering. The earlier author-thesis EPS comparison
is included as a separate context check. The saved means' precise historical
producer and whether their components are independent runs are not established.

The final figure has horizontal values 0.01–0.12 and vertical values 0–14 in
linear minimum SINR. The user-supplied PDF was converted locally to SVG with
Poppler `pdftocairo`; `check_fig4.py` locates the two full-width plot-border
segments, which in this SVG yield top y=427.49609375 and bottom
y=560.42578125 PDF points, with y increasing downward. Each recorded graph
vertex is mapped by `14*(bottom-y)/(bottom-top)`. The figure legend identifies
AP-AO by purple, MR-S-PA by magenta, and MR-TTS-PA by orange. The affine plot
mapping is part of reading its axes; no data-dependent calibration is fitted.
These are drawn vector coordinates with graphical/coordinate rounding, not
the publisher's unrounded ordinate data.

| Method | PDF–MAT maximum absolute difference | PDF–thesis-EPS maximum absolute difference |
| --- | ---: | ---: |
| AP-AO | 0.00025196 | 0.00023965 |
| MR-S-PA | 0.00023819 | 0.00023242 |
| MR-TTS-PA | 0.00016129 | 0.00017116 |

All 36 fixed-ordinal absolute PDF–MAT differences are below 0.0003 in the
plotted linear SINR units. This is evidence that these particular saved
means are graphically compatible with the final publisher artwork. It does
not prove identical underlying numerical data, original solver output,
simulation seeds, all figure curves, physics, convergence, MATLAB/Python
agreement, or full reproduction. The script returns unrounded computed maxima
and RMS values in `recorded-comparison.json`.

The final paper's Table I states U=2. In conversation the user stated that
Figs. 4/5 actually used six LEO users, while the supplied working code also
sets U=6. The mismatch and the source of the saved MAT values remain unresolved;
this graphical match does not independently resolve them. Likewise, the
figure's threshold axis is labeled in watts while the supplied working code
normalizes interference by noise; the known unit boundary is discussed in
`strict/validation/cooperative-author-working-U6-betaR1-dual-full8-20261019-v1/FIG4_FIG5_AXIS_AND_SAVED_MEANS_EVIDENCE_20261030.md`.

## Reproduction of the comparison

Supply the final paper, author ZIP, and existing bounded thesis EPS comparison
report independently; these inputs are not reproduced here. Generate an SVG
for PDF page 13 using `pdftocairo -svg -f 13 -l 13` and a caller-chosen local
output path. Font warnings were observed in the local renderer; axes, curves,
and legend were independently readable on the rendered page. Run:

```text
python -I -B tools/cooperative-fig4-ieee-author-compare-v1/check_fig4.py --fig4-svg /path/to/page13.svg --author-zip /path/to/author.zip --eps-report /path/to/existing-reference.json
```

The script reads the specific local SVG paths, a single ZIP member, and the
earlier small EPS report; it writes only to stdout and does not run an
optimizer, generate channels, extract the author ZIP, or hash source files.
Another Poppler release may represent paths differently, in which case the
strict parser may refuse the input; a mismatch requires review and must not be
automatically interpreted as a scientific failure. The comparison cannot
authenticate historic source contents or show that the PDF was made from the
saved MAT array.
