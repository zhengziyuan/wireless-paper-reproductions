# Explicit author-source errata and exact original-model contract

This package follows the supplied author chapter's non-coherent, independent
satellite-stream/SIC statistical SINR bound (Eq. 4-5), the AP/MR precoder
definitions, full finite-Rician channels, and Algorithms 4-1 through 4-3.
The accessible author manuscript has 16 pages; equivalence to the final IEEE
18-page publication is not established. The following are corrections to the
supplied author equations, **not** a claim that the final publisher PDF has
the same errors. No private manuscript, original artwork, or reference
ordinate is distributed as simulated data.

## Transmit power coefficient in the MR QT problem

The declared statistical MR precoder is `w_ju=sqrt(p_ju)*m_ju`, where
`m_ju=E[h_ju]`. Therefore its physical transmit power is

`sum_u ||w_ju||² = sum_u p_ju ||m_ju||²`.

This is the original physical constraint in Eq. 4-28c. The later Eq. 4-33d
instead prints `sum_u p_ju*s2_juu <= P_T`, with its own definition
`s2_juu=E[|h_ju^H m_ju|²]`. That coefficient equals
`m_ju^H C_ju m_ju + ||m_ju||^4`, not `||m_ju||²`, and cannot be substituted
for transmit power. The code explicitly uses Eq. 4-28c's coefficient and
retains every independent `p_ju` optimization variable. This is a declared
erratum in the same original QT framework, not a fixed-share or alternate
optimizer. In the two-timescale MR case `w_ju=sqrt(p_ju)*h_ju`, the original
Eq. 4-44c instead requires `sum_u p_ju tr(Q_ju) <= P_T`, which is also used.

## GT channel second moment

The supplied chapter defines `alpha` and `beta` as amplitude coefficients
and defines the protected GT interference as `E|g^H w|²` (Eq. 4-8).
Its displayed matrix immediately preceding Eq. 4-14 drops the squares on
both coefficients. For the stated finite-Rician model the exact matrix is
`E[gg^H]=beta² I + alpha² gbar gbar^H`. Both implementations use this full
second moment; there is no instantaneous protected-GT CSI substitution.

## GEO interference and non-coherent indexing

The chapter explicitly specifies independent non-coherent satellite streams
and SIC before Eq. 4-5. The receive-signal lines omit satellite indices on
some symbols. The evaluator therefore uses the original **sum of satellite
powers** bound, not the coherent square of a summed amplitude. The prose's
non-coherent interpretation and Eq. 4-5 identify the intended contract.

An earlier expanded SINR line misses the plus sign before the GEO term;
Eq. 4-11 places `f1 + noise` additively in the denominator. The printed
Eq. 4-12c is not a valid expansion of a direct-plus-cascaded complex amplitude
in general: its cross term cannot be a constant times an absolute square.
The exact contract is the original channel definition
`g=d+G diag(phi) r`, with `f1=E|g|²`, including
`2 Re(conj(mean(d))*mean(G)diag(phi)mean(r))`, all direct/cascaded variance
terms and the GEO power included in the declared channel amplitudes.

## Exact finite-Rician fourth moment

No Gaussian approximation to the product of two NLoS channels is used.
Conditioned on the shared ground channel `r`, the effective channel is
`CN(d+A r, v(r) I)`, with `A=Gmean diag(phi)` and
`v(r)=var(d)+var(G)||r||²`. The exact conditional identity is

`E[||h||^4 | r]=||d+A r||^4 + 2(N+1)v(r)||d+A r||² + N(N+1)v(r)²`.

Integrating this polynomial over the original complex Gaussian `r` gives
the implemented full fourth moment, including NLoS-product terms. The
moment/component receipts and all-coordinate derivative tests validate the
same mathematical channel independently. Different users have independent
RIS-to-user channels; the ground draw for a selected user is shared across
satellites. The Monte Carlo generator retains that dependence.

## Original QT identity and convex subproblem

For either MR case let `A_u=sum_j p_ju*s1_ju` and let `D_u>0` be the original
interference, self-uncertainty, GEO and noise denominator. Then

`A_u/D_u - sum_j [2 y_ju sqrt(p_ju s1_ju)-y_ju² D_u]`
`=D_u sum_j [y_ju-sqrt(p_ju s1_ju)/D_u]² >= 0`.

The original auxiliaries make this tight at the incumbent. All satellite
transmit-power and GT interference inequalities are retained. An exact
positive diagonal change of variable `p=scale*v` conditions the conic
solver but leaves all variables independent and changes no feasible set.
The same identity with complex `z` and the rank-one factor `m^H` is used
for AP. A rank-one desired second moment does not require artificial
Cholesky jitter or a LoS replacement of the interference covariance.

The source's isolated negative-gradient sentence is interpreted as descent
on the negative of its declared maximization objective. The source permits
RGD; the implemented direction maximizes that same original objective.
The squared residual penalty is retained even for satisfied constraints,
not replaced by a hinge. RGD controls and exact stable objective increments
are separately documented in `NUMERICAL_CONTROLS.md`; they are numerical
evaluation changes, not further model/theory errata.

## Certification boundary

Actual source/configuration-bound runs, genuine original stop rules, all
physical/conic/QT gates, original-size baselines and all required figure
points are distinct checks. Passing a component or one complete scenario
does not establish all-sweep or final-publisher curve agreement. Failed or
capped points remain in the result bank and invalidate their selected
figure; no survivor-only average is exported.
