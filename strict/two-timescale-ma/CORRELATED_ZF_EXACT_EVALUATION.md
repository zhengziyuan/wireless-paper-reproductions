# Correlated ZF: exact original-model evaluation, not a replacement covariance

## Source error and scope

The author R2 source, Section V, defines Eq. (68) with **row** covariance
`S(t) in C^(N x N)`. The normalized matrix in Eq. (70) has independent user
columns with covariance `S/(kappa_m+1)`. Equations (72)/(74) multiply this
`N x N` matrix by user-indexed `M x M` matrices. For the original `N=6,M=5`
and `N=8,M=5` scenarios those products are undefined. More fundamentally,
the ordinary noncentral-Wishart step (71) is not valid for arbitrary row
correlation. Thus inserting an identity, trace, effective antenna count,
or a fitted covariance into (74) would change the paper's model/theory.
None is done here. The printed (74)/(75) closed form remains unrecovered.

The new evaluator returns to the paper's **original ZF inverse-Gram and
Jensen argument in (35)/(37)** and evaluates its expectation under exactly
the original correlated channel (68). It does not change AO Algorithms1/2,
the Bessel covariance, the geometry bank, or the supplied NLoS population.
It is a mathematically derived correction/evaluation of the original-model
bound, not evidence that the historical figures14/16 have been recovered.

## Dimension-correct derivation

Write the normalized channel as `X=[x_1,...,x_M]`, with independent
`x_m ~ CN(mu_m,S/(kappa_m+1))` and
`mu_m=sqrt(kappa_m/(kappa_m+1))*hbar_m`. Physical channels are
`H=X diag(sqrt(beta))`. Equal-power unit-norm ZF therefore has

`SINR_m = P beta_m / (M sigma_m^2 [(X^H X)^-1]_(m,m))`.

Condition on the other columns `X_-m`. Let `Q_m` be an orthonormal basis
of their orthogonal complement. Almost surely its dimension is
`r=N-M+1 >=2` for `N>M` and strictly positive covariance. The exact Schur
identity gives

`[(X^H X)^-1]_(m,m) = 1/(x_m^H Q_m Q_m^H x_m) = 1/(z_m^H z_m)`.

Conditionally, `z_m ~ CN(Q_m^H mu_m,C_m)` with
`C_m=Q_m^H S Q_m/(kappa_m+1)`, an `r x r` matrix. For any such Gaussian,
the Laplace identity and nonnegative integral interchange yield exactly

`E[1/(z^H z)] = integral_0^inf det(I+s C)^-1 *`
`exp(-s mu^H (I+s C)^-1 mu) ds`.

This is a scalar positive integral; no Wishart approximation is used.
`correlated_zf.py` and `correlated_zf_inverse_moment.m` evaluate it using
adaptive quadrature after a scale-normalized change of variable from
`[0,infinity)` to `[0,1]`. The separately frozen v3 integrator uses five
deterministic waypoints and tighter working accuracy after an independent
high-precision audit proved endpoint-resolution errors in the old Python
rule. The original declared accuracy and paired acceptance gates are not
relaxed; see [the retained numerical audit](QUADRATURE_ACCURACY_AUDIT.md).
PSD/rank/accuracy errors fail openly, not via
a ridge, clipped eigenvalue, covariance replacement, or shortened bank.

Finally, the original function `g(x)=log2(1+a/x)` has
`g''(x)=a(2x+a)/(ln(2)*x^2*(x+a)^2)>0`. Jensen gives the original-model
theoretical bound `E[g(d_m)] >= g(E[d_m])`, where
`d_m=[(X^H X)^-1]_(m,m)`. `correlated_jensen_bound` averages the exact
conditional moment over **all supplied1000 other-column draws** to
estimate the outer expectation. It records per-user Monte Carlo standard
errors and maximum quadrature error. This finite-ensemble plug-in estimate
is **not itself a guaranteed lower bound on a finite1000-draw sample mean**;
the analytic bound is on the population expectation. Those two claims must
not be conflated.

## Independent checks and execution

The dedicated Python tests have actually passed with the full `N=6,M=5`
Schur check and a **1000-draw** original covariance fixture, plus the
central-iid identity `E[1/||z||^2]=1/(v*(r-1))`, unitary invariance,
channel-scale homogeneity, and explicit non-PSD/rank rejection.

```powershell
python strict/two-timescale-ma/test_correlated_zf.py
```

The corresponding MATLAB analytic and full1000 N6/M5 checks have actually
executed independently. Saved paired evidence separates aggregated/model
agreement from the tighter per-conditional-moment tolerance: one of5000
moments exceeded the fixed1e-9/1e-10 criterion but lay within the combined
reported adaptive error estimates. Such error estimates are not interval
proofs. The analytic entrypoint remains:

```matlab
addpath('strict/two-timescale-ma');
test_correlated_zf_matlab('correlated-zf-analytic-matlab.json');
```

The full exported geometry jobs retain1000 NLoS draws each. Evaluating this
corrected bound on their original iid Algorithm2 trajectories is allowed
only with the label `corrected_original_model_Jensen_bound_not_printed_Eq75`.
It must not be relabeled as the printed closed form, a new correlated
optimizer, or a verified original-figure match. All old blocked-formula
receipts remain historical and untouched.

The [full corrected-source figure adapters](CORRECTED_SOURCE_FIGURES.md)
now evaluate the same exact inverse-moment integral for **both iid and
correlated** models at every unchanged Algorithm2 position, while retaining
the original iid approximation as the design objective. The additional
`spatial_correlation=false` option selects the original iid model, not an
approximation to the correlated model. Default correlated behavior is unchanged.
