# Independent arithmetic on two author-working MAT files

This examines two small, separately saved files from the user-supplied working
author ZIP. It does not run an optimizer, reproduce a figure or validate a
historical numerical experiment. The ZIP is not redistributed here.

The working initialization script sets `P_T(j)=50` for each of three
satellites, enforces the sum of squared beam entries over its 16 antennas and
six users against that limit, and saves `W.mat`. The saved array has shape
`16×3×6`. Interpreting its stored binary64 real and imaginary components as
exact rationals gives powers approximately **44.3124215079**, **1.53e-159**,
and **44.3124189555**, all at or below 50 in the source's power convention.
The nearly zero second value is a property of this saved input, not a claim
about an intended allocation or a general satellite scenario.

The working AO script reads `W.mat` as an initial value and separately saves
`phi.mat`; the latter has shape `25×6`. All 150 saved phase entries are
nonzero. Treating their binary64 components as exact real numbers, none has
exactly unit squared magnitude; the largest absolute squared-modulus error is
approximately **4.16e-16**. This strict bit-level result is not, by itself,
evidence of a physically meaningful unit-modulus violation. No tolerance-based
scientific pass is inferred.

**The two files have different roles and are not established to be a jointly
optimized final pair.** Although the scripts save and load those names, the
historical execution, the matching channel realization, saved point/threshold,
and correspondence to Fig. 4/5 are unknown. Consequently these values cannot
establish the SINR, GEO interference, solver convergence, author-reference
agreement, or a paper-level pass. The original files and prior evidence are
unchanged. The separately reproduced dual-language state capsule is a different
reconstruction and must not be substituted for the author-file channels.

`recorded-saved-wphi.json` contains the exact fractions and derived flags from
one read of each named archive member. The parser accepts bounded little-endian
MAT-v5 complex double arrays and reads the two ZIP members without extraction.
The precise origin and execution time of those files are not authenticated.
The 50 limit is transcribed from the visible working script, not independently
bound to the historical run that produced the files.

From a complete checkout, supply the original ZIP locally:

```text
python -I -S -B tools/cooperative-author-saved-wphi-v1/check_saved_wphi.py --author-zip /path/to/author.zip
python -I -S -B -m unittest discover -s tools/cooperative-author-saved-wphi-v1 -p test_synthetic.py
```

The first command writes only to stdout; the second uses synthetic in-memory
MAT arrays. A matching result does not establish historic provenance or the
remaining scientific gates.
