# Case 13: conditional comparison with the final paper's Fig. 10

This is a **graphical point comparison**, not proof of the author's numerical
inputs, physical feasibility, convergence, or full-paper reproduction. The
comparison uses the user-supplied final IEEE paper, DOI
10.1109/TWC.2023.3309957, Fig. 10 on printed page 3662 (PDF page 15). The
figure's horizontal axis is HU count `U=1,...,6`; its vertical axis is HU sum
rate in bps/Hz with labeled limits 2 and 14. Its legend writes the satellite
Rician factors as linear values `beta_S=1,10,100`; the case-13 setting
`20 dB` nominally corresponds to `beta_S=100`.

## Source-figure reading method

The final PDF page was rendered to SVG locally with `pdftocairo`; neither the
rendered page nor the source image is redistributed here. The graph's left
axis is at approximately `x=79.9922` PDF points (`U=1`), its right axis at
`x=281.4805` (`U=6`), and the vertical plot borders are approximately
`y=79.62109` for 14 and `y=212.92188` for 2, with y increasing downward.
The source-figure values below use the first vertex of each `beta_S=100`
solid six-point polyline and the affine conversion

`rate = 2 + 12*(212.921875 - y)/133.30078125`.

The legend identifies AO as the red solid line with downward triangle,
TwoStage as the magenta solid line with square, and NoRIS as the blue solid
line with crossed marker. The corresponding first-vertex y coordinates are
approximately 159.16016, 151.31250 and 194.49609 PDF points. A conservative
display-reading allowance of about `±0.05 bps/Hz` covers roughly half the
0.771-point curve stroke plus graphical coordinate rounding. It is not a
formal bound on the author's original data, figure-generation rounding, or
statistical error. These are graphic-derived approximations, not exact data.

| Scheme | Fig. 10 graphical reading | Saved case 13 empirical-power ratio rate | Saved case 13 mean `E[log]` estimate |
| --- | ---: | ---: | ---: |
| AO | about 6.84 | 10.569907695260937 | 10.570596972343877 |
| TwoStage | about 7.55 | 10.56990832692759 | 10.570597459522535 |
| NoRIS | about 3.66 | 4.73447853200738 | 4.731317681185383 |

The graphical reference is below both saved quantities in all three rows.
The two saved columns must not be treated as the same metric: the first uses
a ratio of empirically averaged powers, while the second averages sampled
log-rates. The paper formulates its statistical-CSI objective using an
expected-power approximation; the historical figure's actual sample
generation and plotting data are not available here. A finite empirical-power
ratio is not automatically identical to that theoretical quantity.

The nominal labels `U`, `beta_S`, and scheme are insufficient to establish
identical algorithms, normalized channel parameters, author coordinates or
random realizations. In particular, the public implementation documents the
printed scalar-SOC inconsistency and its explicitly labeled vector-QT
correction, plus an unresolved early-ESA versus later-isotropic channel-moment
scope difference. Original author geometry and historical producer identity
remain unauthenticated. The saved MC case itself does not prove sample
independence, full physical feasibility or MATLAB/Python agreement. The
comparison therefore reports an observed reference mismatch under these
boundaries; it neither diagnoses an error in the author's figure nor claims a
scientific PASS. See `strict/hotspot-satcom/STATISTICAL_ERRATUM.md` and
`validation/hotspot-case13-final-mc-v1/README.md`.

`recorded-comparison.json` retains only the three transcribed points, axis
coordinates, computed comparisons and scope flags. From a complete checkout,
`python -I -S -B tools/hotspot-case13-fig10-comparison-v1/verify_graph_comparison.py`
recalculates these comparisons against the already published compressed
case-13 projection. The script does not read or redistribute the paper and
does not independently authenticate the transcribed figure coordinates or
legend mapping. Both the figure reading and any runtime differences require
independent review.
