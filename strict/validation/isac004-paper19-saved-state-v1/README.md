# Eq. (19) gain correction: one saved ISAC004 NoRIS state

This package checks the power expansion in **arXiv:2512.20987v2 (28 February 2026)**, [Eqs. (14), (18), (19), (21)–(23)](https://arxiv.org/html/2512.20987v2#S2.SS4). It contains only the six saved numerical arrays and the geometry, gain, wavelength and previous scale needed for this replay. It creates no channels, samples or optimizer iterates.

Write `v = B diag(theta) t_R` and `Q = W W^H`. Equation (14) gives `f = sqrt(G_B) t_B + sqrt(G_R) v`. Thus Eq. (18) expands to

```text
G_B * t_B^H Q t_B
+ 2 * sqrt(G_B * G_R) * Re(t_B^H Q v)
+ G_R * v^H Q v.
```

The printed Eq. (19) instead uses `1` for the direct term coefficient and `sqrt(G_B * G_R)` for the reflected-power coefficient. The correction is algebraic; the middle coefficient is unchanged. Other manuscript versions have not been checked by this package.

The saved state is a NoRIS baseline with a zero bridge. Its two desired directions lie in the BS back hemisphere. The paper's gain model makes their gain and Eq. (18) powers zero, while applying the printed direct term gives positive powers. The replay independently reconstructs the gain-free steering vectors from the saved geometry and compares all 66 corrected direct powers with saved powers. **A nonzero-RIS state has not been numerically verified here**; the reflected-term correction follows from expansion of Eqs. (14) and (18).

For `c = p^T p > 0`, `d = p_d^T p >= 0`, `e = p_d^T p_d > 0`, finite positive `iota`, and the paper's positive safeguard `epsilon`, its practical update is `iota_epsilon = c/(d+epsilon)`. The same normalized error as paper Eq. (22) yields `NMSE_epsilon = 1 + (epsilon^2-d^2)/(e*c)`. For `d>0`, the excess above the finite exact minimum is `epsilon^2/(e*c)`; for this saved state `d=0`, every finite positive `iota` has `NMSE > 1` and the infimum `1` is approached only as `iota` tends to positive infinity. At fixed `p` and `p_d`, the safeguarded update is non-increasing relative to a positive previous `iota0` precisely when `epsilon <= abs(c/iota0-d)`. The computed bound is state-specific: the paper does not specify the author's numeric epsilon, and the bound is not an author parameter or an AO convergence proof.

Install Python 3 and NumPy, then run with a **new, nonexistent** output path. No original evidence or other file is overwritten.

```text
python replay.py --input-dir . --output /path/to/new-output.json
```

The output reports the exact decimal interpretation of the saved binary64 `p` and `p_d` values and uses floating-point arithmetic for the steering reconstruction. It checks only this state. The original failure, incomplete trajectory, MATLAB/Python verification, full published scenarios, convergence and original-figure agreement remain unresolved; this package is not scientific acceptance of a case or paper.
