# MIS sensing: saved 6,000-start Figures 3, 5, and 6 evidence

This capsule provides real saved-data figures, one selected native state, the
assembled curves, and a small deterministic regeneration interface. It does not
claim agreement with the original paper's curves, complete dual-language figure
verification, or convergence of every initialization.

The source-bound native population contains 6,000 initializations: 5,280 saved
combined certificates are true and 720 are false. The frozen implementation's
selector chooses original initialization 3072, whose combined certificate is
**false**. Every initialization, including all 720 false outcomes, contributes to
the saved means. No passing subset was substituted.

## Included results and selection

- [Figure 5](figures/Fig5-saved-fixed-selection.png) and
  [Figure 6](figures/Fig6-saved-fixed-selection.png) use the same selected 3072 and
  all 6,000-start means. PDF and SVG versions accompany both PNGs.
- Figure 3 has nine target panels, named `figures/fig3-target-1.png` through
  `figures/fig3-target-9.png`. Each contains normalized gain and echo SINR on a
 91 by 361 grid. The saved native phases and schedule were evaluated
  deterministically with the disclosed Python field formulas.
- `data/selected-fixed-final-state.json` contains the selected phases,
  placement, settings, metrics and actual outer history.
- `data/fig5-fig6-saved-curves.json` contains all 30 curve slots.
- `data/assembly-summary.json` and the small `evidence/` files record the scope,
  failures, code identities, actual field/display executions and visual review.

The selector is the frozen implementation's relaxed-primal-feasible maximum of
final eta: `maximum_constraint <= feasibility_tolerance`, then strictly larger
eta, retaining the earliest original ID on ties. It does not first filter for
combined convergence or binary feasibility. This is a disclosed implementation
rule; the author's exact output selection rule was not recovered.

All 6,000 actual histories in this extraction contain 30 outer iterations. No
derived hold was applied. The general implementation can hold the last state of
a shorter history, but that policy is not evidence that it occurred here. Eta is
linear. Figure6 uses `max(0,max(q))`; it is not presented as a recovered author
violation norm. Exact zero residuals remain zero. On the log display they appear
as bottom-axis markers and gaps, with positive samples drawn as small circles
so isolated positive samples remain visible.

For selected 3072, the saved final primal, domain, binary and KKT subgates pass,
but one earlier inner iteration-cap exit makes the saved all-inner/combined
certificate false. Its exact outer iteration/block was not recorded. The
final reason is `gradient_tolerance`. See
[the selected witness](evidence/selected3072-saved-convergence-subgates.json).
This single-state witness neither explains all 720 false outcomes nor establishes
an error in the original paper.

## Physical convention and remaining gates

The saved cohort uses the literal reference level -73.88 dB, interpreted as
inverse watt, raw noise per PRI, effective gain 1, and 30 dBm transmit power. A provisional clarification supports the raw-per-PRI interpretation. The
inverse-power reference unit and effective processing gain remain unverified;
the clarification does not establish a factor 100, a 20 dB correction, a PRI count,
or any additional array/processing factor. No such adjustment or reference fit
was applied.

Figure 3 uses the frozen independent 1 degree grid: azimuth -180..180 degrees and
elevation 0..90 degrees. The grid, selection and normalization are disclosed
reconstruction conventions, not recovered author output rules. The very small
agreement between the deterministic field evaluation at target directions and
the stored native binary metric is a same-state consistency observation. It is
not a complete MATLAB/Python figure campaign or an original-reference gate.

Original-reference agreement, dual-language figure agreement, all 6,000 original
combined convergence, and whole-paper completion remain false. The original
6,000 banks, individual proof bodies, authors' PDF, and 22.7 MB full-grid JSON are
not redistributed. The capsule therefore cannot independently reselect the
whole population or recompute its mean from individual starts. It can reproduce
the saved curve displays and compute Figure 3 fields from the included state.

## Regenerate from the packaged state and curves

Python 3.10 or newer, NumPy and Matplotlib are required. Run from this directory
and choose a fresh output directory outside the capsule:

```console
python -X utf8 -B sources/regenerate_saved_outputs.py --mode curves --output ../my-saved-curves
python -X utf8 -B sources/regenerate_saved_outputs.py --mode fields --output ../my-saved-fields
python -X utf8 -B sources/regenerate_saved_outputs.py --mode all --output ../my-saved-figures
```

`curves` renders Figures 5/6 from saved ordinates. `fields` writes the complete
Figure 3 grid from saved 3072 without optimization or random draws. `all` also
renders the nine Figure 3 panels. The full-grid calculation allocates the full
angular arrays; no reduced grid, optimizer, initialization, MC, MP audit or
reference fitting is substituted. Figure 3's frozen renderer clips only its dB
display at -120 dB and leaves the stored samples unchanged.

The field kernel's three numerical functions retain the exact source/AST from
the actual evaluator. The Model and normalization libraries and the frozen
Figure 3 renderer retain their exact bytes. The Figure5/6 renderer is the actual
V2 source that fixed invisible isolated positive log samples. The new public
host only supplies relative paths and source/input closure. The first actual
portable `--mode all` execution returned naturally with code0. All nine panels
of regenerated full-grid samples were numerically identical to the prior actual
field output, and all11 PNGs had pixels identical to the original figures already
visually reviewed. All six Figure5/6 output formats were present. See the
[actual portable execution receipt](evidence/portable-first-use-and-exact-output-comparison.json).
The source and saved inputs remained unchanged. This closes the saved-state
regeneration interface check; it does not establish the outstanding original
reference or dual-language figure gates. Execution-session identifiers in the
receipt are local observation labels, not reader-accessible public endpoints.

`SOURCE_AND_ARTIFACT_MANIFEST.json` identifies every file except itself. Only
private absolute metadata paths were replaced in the portable saved JSON;
numerical values, arrays and failed flags were preserved. Opaque
`undistributed/local-identity-*` entries describe original private evidence and
do not name files available in this capsule. Their hashes are provenance, not a
replacement for access to the original 6,000 data.
