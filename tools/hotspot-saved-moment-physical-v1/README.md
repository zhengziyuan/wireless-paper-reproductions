# Conditional check of one saved hotspot design

`verify_saved_design.py --result RESULT.json` independently reconstructs the
declared geometry and finite-Rician channel moments for one saved AO design,
then reads its saved phase and beam matrix and recomputes all signal-to-
interference ratios, total power and HU sum rate. It sums every interfering
stream directly and evaluates the ESA Bessel pattern with a high-precision
decimal power series; it needs NumPy, but not SciPy or an optimizer.
This is a quantitative diagnostic: it reports differences and margins, but it
does not apply a numerical agreement threshold, assign a PASS, or return an
error solely because saved and recomputed numerical values differ. Inspect the
reported values and their assumptions before drawing any conclusion.

For `statistical-validated18-final/U3-beta20/AO-start0.json`, the saved
16-feed/16-stream design has 13 NHUs. On this machine the total power was
approximately 99.999999998 W versus 100 W, the smallest NHU ratio was about
0.5011872374 versus the declared −3 dB threshold 0.5011872336, and the
recomputed HU sum rate was about 11.0943017 bit/s/Hz. The finite floating-point
margin is only about 3.7e-9; this is not a rigorous interval feasibility proof.

The input is reconstructed from the saved configuration under the existing
scenario geometry and noise assumptions. Matching serialized output does not
authenticate which historical code or inputs actually ran. The all-stream
interference denominator is the explicitly disclosed physical correction to
the paper's K-only printed statistical formula. The calculation does not
verify old inner iterates, convergence, fixed-auxiliary solver constraints,
MATLAB, the authors' historical figures or the complete paper. It does not
modify inputs, create new channel samples or write output files.
