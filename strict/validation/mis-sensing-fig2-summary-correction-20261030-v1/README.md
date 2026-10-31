# MIS sensing Fig. 2: correction to the reproduction summary

The earlier reproduction summary in [ALL_PAPERS_ISSUES.md](../../ALL_PAPERS_ISSUES.md), lines 293–303, states **2.8050 dB** for the second target. Its linked [complete-map verification receipt](../sensing-correctness-v4/figure02-all9-full-map-independent-matlab-python-check.json#L143-L153) instead records **0.8050065155970396 dB** as the second entry of `target_sinr_db`. The earlier summary value is inconsistent with that receipt and should read **0.8050065 dB** when referring to this recorded calculation.

This corrects our reproduction documentation, **not the original paper**, its formulas, or its plotted values. The calculation that originally motivated the 2.8050 dB wording has not been established. The discrepancy is not evidence of a physical 2 dB correction, an additional processing gain, or a changed noise level. The existing summary and numerical receipt are retained unchanged; this note supplies the correction separately.

## Quantity and target identity

The repository's [independent finite-array checker](../../compare_sensing_closed_form.py#L68-L80) orders targets with azimuths `[0, 45, 90]` degrees within each elevation `[30, 50, 70]` degrees. The second target is zero-based index 1: **azimuth 45 degrees, elevation 30 degrees**. Its metric is target echo power divided by the sum of every other target's echo power and the noise term. It is target SINR, rather than normalized pattern gain or PSLR. The checker [explicitly applies `10*log10`](../../compare_sensing_closed_form.py#L135) to these power-ratio metrics in target order when forming `target_sinr_db`.

The [recorded receipt](../sensing-correctness-v4/figure02-all9-full-map-independent-matlab-python-check.json) identifies all nine full-scene analytical panels, 400/256 surface elements, 25 placements, and the independent MATLAB/Python comparison. Its stored second-target value, the target definition, and the dB conversion support the documentation correction without repeating the calculation.

## Normalization and acceptance boundaries

The checker [requires the declared contract](../../compare_sensing_closed_form.py#L50-L58): inverse-watt reference, raw-per-PRI noise, effective reference gain 1, one BS antenna, 30 dBm = 1 W, and a reference level of -73.88 dB. Raw single-PRI noise remains a **provisional interpretation of the historical setup**. Neither its tentative clarification nor this receipt establishes the original inverse-power reference unit or any effective processing factor. See [SIGNAL_NORMALIZATION.md](../../mis-sensing/SIGNAL_NORMALIZATION.md). The separate factor-100 candidate is not promoted to an author-confirmed parameter.

The prior receipt verifies the complete analytical Fig. 2 calculation under that declared convention. It explicitly leaves original-figure certification and completion of all iterative figures false. Full published-figure/reference agreement, all required 6000-start campaigns with their original 30 outer/4000 inner budgets, convergence, and the historical reference-unit/processing contract remain unresolved. This note performs no new optimization, integration, simulation, or numerical acceptance test.
