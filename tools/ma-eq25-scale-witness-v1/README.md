# MA paper Eqs. (25), (27), and (28): missing curvature scale

The final IEEE version of *Two-Timescale Design for Movable Antenna-Enabled
Multiuser MIMO Systems* ([DOI 10.1109/TCOMM.2025.3585515](https://doi.org/10.1109/TCOMM.2025.3585515)), printed page 10560, defines the Hessian of `b_m` in Eq. (24), the symmetric matrix `Psi` in Eq. (26), and the same matrix in Eqs. (25), (27), (28), and (29). The Hessian in Eq. (24) includes a factor `s = 8*pi^2/lambda^2`, whereas the entries of `Psi` in Eq. (26) do not. Nevertheless, the displayed inequalities in Eq. (25) and Eq. (27) compare the Hessian to the unscaled matrix norms, and Eq. (28) defines the two curvature bounds by the same unscaled norms. Eq. (29a) subsequently includes the factor `s`. These printed definitions are inconsistent.

Using the matrix defined by Eq. (26), the scale-consistent inequalities are

```text
||H||_2 <= ||H||_F <= s ||Psi||_F
||H||_2 <= s ||Psi||_2 <= s ||Psi||_F.
```

The last norm inequality retains the comparison intended in Eq. (28), with both curvature values scaled by `s`. In this model the coefficients in Eq. (26) are nonnegative, and each contribution to `Psi` is an outer product of the two absolute direction differences, so `Psi` is positive semidefinite. Thus its spectral norm is its largest eigenvalue, making Eq. (29a) consistent with the scaled second bound. The separate sign error in the printed closed form Eq. (29b) is documented in [the Eq. 29 witness](../ma-eq29-saved-witness-v1/README.md).

For a concrete example, the companion script uses the same [saved Fig. 5 input](../ma-eq29-saved-witness-v1/saved-input.json) as the Eq. 29 check, without new optimization or random samples. It evaluates all 30 Hessians from Eq. (24) and all 30 matrices from Eq. (26). With the saved `lambda=1`, the printed unscaled Eq. (25) Frobenius bound and Eq. (27) spectral bound both fail in 30/30 cases; the bounds multiplied by `s` hold in these computed values. At antenna 6, user 3, `||H||_2 = 5.078366974834155e-7`, `||Psi||_2 = 6.912788268987873e-9`, and the ratio is about 73.4634, below `s = 8*pi^2` once the factor is included. A central difference of the separately computed Eq. (22) gradient for that Hessian gives relative max error approximately `1.43e-9`.

From this directory, with Python 3 and NumPy, use a fresh output path:

```sh
python -B check_eq25_scale_witness.py ../ma-eq29-saved-witness-v1/saved-input.json /path/to/new-report.json
```

All matrices and comparisons are computed in binary64 and are not a rigorous interval certificate for the physical model. The algebraic prefactor discrepancy follows directly from the printed definitions; this example only illustrates its numerical effect in one saved input. It does not prove or invalidate the entire optimization, dual-language reproduction, figure, or paper.
