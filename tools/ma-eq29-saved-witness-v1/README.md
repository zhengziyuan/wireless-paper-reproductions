# MA paper Eq. (29): saved-state matrix witness

The final IEEE version of *Two-Timescale Design for Movable Antenna-Enabled
Multiuser MIMO Systems*, DOI [10.1109/TCOMM.2025.3585515](https://doi.org/10.1109/TCOMM.2025.3585515),
defines the real symmetric matrix `Psi = [[a,b],[b,d]]` in Eq. (26) and its
largest eigenvalue in Eq. (29a). On printed page 10560, Eq. (29b) prints
`sqrt((a-d)^2 - 4*b^2)`. This is a sign error: the characteristic polynomial
`x^2-(a+d)x+(a*d-b^2)` gives the discriminant `(a-d)^2 + 4*b^2` and hence

```
lambda_max(Psi) = (a + d + sqrt((a - d)^2 + 4*b^2)) / 2.
```

Thus the positive discriminant agrees with Eq. (29a); selecting Eq. (29a)
preserves the stated upper-bound construction. This diagnosis is about the
printed equation, not an experimentally inferred change of algorithm.

The compact [saved input](saved-input.json) contains the source-generated
geometry parameters and saved final MRT antenna positions for one retained
Python Figure 5 case: `N=6`, `M=5`, `kappa=100`, point 30, realization 0.
It does not include fading samples, optimizer histories, or the paper PDF.
The check builds all 30 Eq. (26) matrices from those values without an
optimizer or random draws. Exactly 24 of their printed-minus discriminants
are negative for the computed binary64 entries. For antenna 1 and user 1,
divide the matrix by its largest entry, approximately `2.89610799825e-9`:

```
Psi / scale = [[0.4737467288111990, 0.5029644956604331],
               [0.5029644956604331, 1.0000000000000000]]
printed-minus discriminant = -0.7349506301429016
correct-plus discriminant  =  1.2888356410167290
correct maximum eigenvalue of Psi / scale = 1.3045078508968468
```

For these 30 matrices the largest relative difference between the correct
closed form and `numpy.linalg.eigvalsh` is about `2.1e-16`. The repository's
MRT kernel uses a denominator scaled by the positive user coefficient
`beta[m]`, so its internal matrix is `beta[m] * Psi`. The check constructs
that matrix separately and confirms the relation to within about `3.4e-16`
relative in this saved example. Its scale must not be confused with the
paper's unscaled `Psi`.

From this directory, with Python 3 and NumPy, use a fresh output path:

```sh
python -B check_eq29_saved_witness.py saved-input.json /path/to/new-report.json
```

The script computes signs exactly as rational expressions of its computed
binary64 matrix entries; the reconstructed model values themselves have no
interval-certified forward-error guarantee. The witness illustrates the
equation inconsistency in one saved input; it does not verify the whole
Figure 5, convergence, the MATLAB results, or the original reference curve.
