# Explicit statistical-CSI erratum and exact original-model corrections

These corrections concern the supplied author thesis, equations 3-41 through
3-57. Equivalence to a different final publisher version is not asserted. The
printed-algorithm entry raises an explicit error; the working entry is labelled
`corrected_QT_erratum`. The working physical branch retains the **early ESA-
weighted finite-Rician signal model**, average-SINR QoS, sum-rate objective,
power constraints, full scenario dimensions and phase unit-modulus constraints.
This does not make the later scalar-isotropic covariance formula a literal
recovery: the source-model scope inconsistency below must remain explicit.

## Scope of the original RGD guarantee

The preceding single-HU discussion claims that its printed augmented matrix
is positive semidefinite and that a nondecreasing RGD sequence consequently
converges to a global optimum. Neither implication holds in general. The
printed matrix has the block form `[C,b; b^H,0]`; any nonzero entry b_j gives
the principal minor determinant `-|b_j|²<0`. Restoring the omitted constant
diagonal can form a positive-semidefinite Gram matrix, but does not remove
the nonconvex unit-modulus feasible set. Adding a sufficiently large identity
matrix makes any Hermitian quadratic positive semidefinite while adding only
a constant on this set. PSD is therefore not a global-optimality certificate.
Even `ones(2,2)` has zero Riemannian gradient at `[1,-1]`, with objective0
versus4 at `[1,1]`. Production preserves the original RGD and its real stop
flags but makes no general global-optimality claim. This is a limitation of
the stated theorem/argument, not a reason to replace the original optimizer.

Source anchors are `ch_third.tex:349-353` (printed block with zero last diagonal)
and `ch_third.tex:390` (PSD, monotonicity and global-optimality claim). They are
anchors in the supplied author thesis, not verified final-publisher locations.
The reproducible independent check is `audit_single_hu_guarantee.py`; its actual
receipt `outputs/single-HU-guarantee-counterexamples.json` records determinant
−1 and eigenvalues approximately −0.618034 and1.618034 for `[1,1;1,0]`. For the
PSD all-ones matrix, the original circle-projected gradient at `[1,-1]` is
exactly zero, objective0, whereas `[1,1]` attains4. Adding identity makes the
matrix strictly positive definite with eigenvalues1 and3, but the same
stationary/global objectives become2 and6; the gap is unchanged. With the
augmented coordinate fixed to1, the equivalent stationary vector is `[-1,1]`.
These are mathematical counterexamples to a general guarantee, **not** small
substitutes for the original full-scene simulations or evidence of an author
initialization. The existing original full-size RGD is not replaced.

## 1. The stated full-rank average-SINR QoS is not the printed scalar SOC

Let `Q_k = E[h_k h_k^H]`, `D_k^H D_k = Q_k`, and
`I_k(W) = sum_{j != k} ||D_k w_j||² + sigma²`. The correct QoS is
`||D_k w_k||² / I_k(W) >= tau_k`. The interference index is all transmitted
streams J, as uniquely follows from the received signal before 3-41; the K-only
denominator in 3-41b omits HU interference and is an explicit index erratum.

For every vector b, completing the square gives the exact identity

`||D_k w_k||²/I_k - [2 Re(b^H D_k w_k) - ||b||² I_k]
 = I_k ||b - D_k w_k/I_k||² >= 0`.

Consequently the covariance QoS is **exactly equivalent** to existence of b
with `2 Re(b^H D_k w_k) - ||b||² I_k >= tau_k`. The optimal auxiliary is
`b = D_k w_k/I_k`, the same vector quadratic transform already used for the
HU objective in 3-43/3-45. For fixed b this is a convex quadratic/SOC constraint.
The erratum therefore applies the original vector-QT machinery to QoS too,
rather than pretending a full-rank desired quadratic has a scalar phase gauge.

At a feasible current W, updated b makes this lower bound tight. The current
W is feasible for the next convex block; every new point satisfies the original
covariance QoS because its exact SINR is at least the enforced QT lower bound.
The HU objective has the corresponding tight global lower bound, so an exact
block solve cannot decrease its original objective. This proves feasibility
preservation and monotonicity; it does not assert global optimality.

This explicitly adds QoS auxiliaries missing from the printed 3-46 algorithm.
It is a mathematical erratum within the original QT framework, **not** a claim
that the author used these missing updates to generate the historical figure.
Original printed 3-46 incorrectly uses `||i w||²` to subtract `||w||²` and uses
`1_N^T w` where a vector norm is needed. No imaginary coefficient can repair
the former: `||i w||² = ||w||²`. The earlier counterexample remains valid.

## 2. Exact channel moments, with shared satellite-to-RIS fading

### Model-scope inconsistency: early per-feed ESA versus later scalar mu

The early source defines `H=Hbar o D`, IID unit-variance NLoS in `Hbar`, and
the feed-dependent ESA gain `D_np`; see `ch_third.tex:34-52`, especially
lines35-46. Therefore for a user p and finite beta the signal model uniquely
implies

`h_p = D_p o [sqrt(beta/(1+beta)) a_p + sqrt(1/(1+beta)) e_p]`,
`Cov(h_p) = diag(D_1p²,...,D_Np²)/(1+beta)`.

The later Section3.5 writes one scalar large-scale coefficient mu per link
(`ch_third.tex:484-492`) and `mu/(1+beta) I_N` in the NHU moment (line515,
equation3-42b). These expressions coincide with the early ESA-weighted model
**only if all squared per-feed gains for that link are identical**, or if a
separate normalized/isotropic statistical model is explicitly assumed. No
such reduction or equal-gain condition is stated in the supplied source.
It is a model-scope contradiction / unreported simplification, not proof that
the author intentionally used a particular alternative mu. The general
physical diagonal-covariance implementation is mathematically correct for
the early signal model, but is **not literal printed3-42 recovery** and is not
evidence that it generated the historical statistical curve.

`audit_covariance_contract.py` supplies an independent no-optimizer audit.
The actual full16-feed/U6/K10 source-compliant-distance fixture in
`outputs/source-covariance-contract-audit.json` gives nearest-isotropic relative
Frobenius errors0.865657 for HU links and0.968210–0.968221 for NHU links. For
variance vector v, minimizing `sum_n (v_n-c)²` has the unique solution
`c=mean(v)`, so these are lower bounds on the discrepancy for **any** scalar
variance, not fitted author parameters. 20000 independent proper-CN draws per
link verify the nonuniform diagonal variances (maximum relative sampling
error0.018654). The nearest scalar is retained only as diagnostic evidence;
it is neither substituted into production nor selected to match a reference.

The deterministic per-feed LoS mean and author array/footprint coordinates
are separately unrecovered. A declared common-path phase reconstruction must
not be conflated with the source's angle-dependent array response. Fixing the
HU pair-distance violation only validates that individual distance contract;
it does not certify every original geometry, covariance, mean or figure.

### Exact moments for the explicitly declared early physical model

For the original row channel `c_u = d_u + sum_m phi_m r_um G_m`, independent
proper complex Gaussian NLoS terms with their stated finite-Rician means and
variances give

`mean(c_u) = mean(d_u) + sum_m phi_m mean(r_um) mean(G_m)`;

`Cov(c_u^H) = diag(var(d_u))
 + sum_m var(r_um) mean(G_m)^H mean(G_m)
 + diag(sum_m var(G_m) [|mean(r_um)|² + var(r_um)])`.

The second moment is this covariance plus `mean(c_u)^H mean(c_u)`. This is the
full covariance, not a LoS-only approximation. Unit-modulus phases make this
covariance phase independent; their mean outer product retains the full phase
dependence. It reduces to 3-42 under its common-variance/rank-one-LoS assumptions.
The isolated repeated beta_S square root on the source's G_NLoS term conflicts
with the stated unit-normalized Rician model and 3-42; the independent variance
is the model's `mu/(1+beta_S)`, not a second LoS gain.

The rate quantity remains the source approximation `log2(1+ratio of expected
powers)`; it is not mislabelled as an exact ergodic expectation of log rate.
The phase rate in 3-48 includes noise in numerator **and** denominator, exactly
as implied by `1+SINR`. Derivatives come from these original moments.

## 3. Do not exchange expectation and division in normalized NHU projectors

Define `P_k = h_k h_k^H/||h_k||²`, so `P_k²=P_k`. NHUs are independent. For
`A = I-sum_k P_k`, the exact moment is

`E[A A^H] = I-sum_k E[P_k] + sum_{k != l} E[P_k] E[P_l]`.

For `h ~ CN(m,C)`, use `1/x = integral_0^infinity exp(-t x) dt`. With
`L(t)=det(I+tC)^(-1) exp(-t m^H(I+tC)^(-1)m)`,

`E[P] = integral L(t) [(I+tC)^(-1) C
 + (I+tC)^(-1) m m^H (I+tC)^(-1)] dt`.

Both implementations use the identical dimensionless one-dimensional integral
after scaling by `E||h||²`. This preserves trace1 and is invariant to path gain.
The source's printed gain-dependent unnormalized covariance product is not
substituted for this normalized expectation.

For HU pairs, the satellite-RIS G is shared. The fourth moment is evaluated
by conditioning on the independent ground channels r_u,r_v. The conditional
joint Gaussian identity is

`E[|x^H y|² | r] = |b_x^H b_y + tr(C_yx)|²
 + b_x^H C_yy b_x + b_y^H C_xx b_y + tr(C_xx C_yy)`.

Its r-averages are exact complex-Gaussian bilinear moments. In particular
`B = A^H A + diag(sum_n var(G_mn))` in the bilinear term retains the shared-G
contribution absent from an independent-cascades approximation. The published
code differentiates that exact polynomial, not a sampled surrogate objective.

## 4. Conditioning is separate from a mathematical erratum

### ESA amplitude/power convention is explicit, not literal equation3-3

`ch_third.tex:44-52` places `G_T` under a square root in the channel-amplitude
gain, but displays `J1(nu)/(2nu)+36 J3(nu)/nu³` without a square or maximum
gain factor. The Bessel sum is an amplitude pattern and can be negative:
at nu7 it is−0.0179204966273, so it cannot itself be a physical power gain.
The unchanged generators explicitly use `Gmax*abs(BesselSum)²`. This is a
disclosed physically nonnegative amplitude-to-power interpretation, not
literal unsquared equation3-3 recovery. Whether the source omitted a square,
used separate normalized-gain notation, or differs from its final IEEE version
is unverified; no author historical convention is inferred from curve fitting.

An independent primary-paper example defines beam **power** gain as the
squared sum times Gmax in [Section2.1, equation3 of Wang et al. (2020)](https://link.springer.com/article/10.1186/s13638-020-01749-7).
It supports this amplitude/power distinction, not final-text equivalence for
the user's paper. `audit_esa_pattern_contract.py` records the independent
counterexample and124 negative literal entries in the current272-entry
full16-feed scene in `outputs/esa-pattern-contract-audit.json`; it does not
alter a channel, tune an optimizer, or inspect reference ordinates.

The cited [Christopoulos et al. author preprint, SectionII-A/p8](https://arxiv.org/pdf/1406.7699)
does explicitly discuss a same-per-user phase across satellite feeds as a
common long-path multibeam-channel assumption. This makes the assumption
plausible, but still does not recover the deterministic means/array responses
actually chosen in the user's later statistical section or historical figure.

The original channel-gain equation 3-2 already divides satellite links by
`sqrt(kappa*T_R*BW)`. In these noise-normalized coordinates the effective
receiver variance is one. Dividing the channels or the F2/F3 criterion by the
physical noise again would change the source model and is not done. The
original numerical paragraph fixes equal RIS-to-HU path loss at the common
400m reference distance; actual HU offsets are retained only in the phases.

For the instantaneous QT/SOCP, lambda and gamma epigraphs are monotone and
attain equality at optimum. Eliminating them exactly leaves the same conic
optimization objective and physical feasible set. With `c_u=1+q_u(W_current)>0`,
`log((1+q_u)/c_u)+log(c_u) = log(1+q_u)`. This positive affine scaling of the
exponential-cone argument avoids large high-SINR coefficients without changing
the objective. Numerical backend regularization retries solve the same block;
each attempt retains physical feasibility and exact objective residual checks.
No users, constraints, or covariance terms are dropped and no stopping threshold
is loosened. These numerical controls are explicitly not recovered author data.

The original RGD gradient direction, retraction and Armijo sufficient-increase
test are unchanged. Its unreported initial step is `1/||grad F||`, giving a
unit initial tangent displacement before the original halving search. The
gradient stopping threshold remains `1e-6`, and exhausted 5000-iteration
blocks are not marked converged. Old alpha-one iteration-cap receipts are
retained as numerical-control diagnostics, not used as successful certificates.

The preferred independent spectral branch uses alternating positive BB1/BB2
curvature values only to choose an initial scalar step for this same original
gradient and halving search. Exact polynomial increments and `log1p` ratio
increments prevent cancellation near stationarity; they are algebraic
identities for the original objective, not roundoff slack in Armijo. The
unreported safety cap of the spectral/single-start geometry branches is20000
after preserved actual5000-cap failures. That distinct source-distance-
compliant full18 bank retained a genuine U6/beta0 two-stage failure at20000:
gradient4.2992924454e−6 exceeds the unchanged1e−6 threshold. An independent
same-start, same-model, same-direction/retraction/Armijo rerun with declared
100000 cap reached9.99935061084e−7 at39910 iterations in334.2254s; see
`outputs/source-geometry-U6beta0-phase-budget-python.json`. The new validated
branch declares100000 only as an unreported safety cap. A cap is never
accepted as a stopping rule; neither the old failure nor the isolated phase
test is upgraded into completion of all schemes or all figures. This numerical
control is separate from the explicitly labelled vector-QT theoretical erratum.

### Uniform declared starts, not a selected-success certificate

`statistical_validated_config.json` and `statistical_ensemble.py` apply one
predeclared0..U initialization policy to **every** NoRIS/two-stage/AO scheme.
Start0 is the conservative original feasible symmetric point. Starts1..U
retain every NHU beam and restore the corresponding existing HU beam direction
at the maximum remaining power permitted by all original NHU average-SINR
constraints. The exact interference-slack proof is implemented in Python and
MATLAB; the old local-basin diagnostic is not itself a production baseline.
Phase seeds for two-stage/AO are one language-independent SHA256 schedule.
NoRIS has no phase variable and uses the same start IDs and beam rule.

Every declared start executes the entire original QT/RGD/outer chain and saves
its physical evaluation, initial/final states, objective history, original
block stops and numerical gates. The largest final original approximate
sum-rate chooses a fixed design only among genuinely completed feasible
trajectories. **Any** missing, failed, capped, or bound-violating required
start makes the corresponding ensemble and full point fail, regardless of the
quality of a selected other start. Tests explicitly reject these cases.
Exactly1000 fresh paired channels evaluate each selected fixed design; this
is neither an average over initializer starts nor a survivor-only MC mean.
The initialization policy is disclosed numerical control, not recovered
historical author settings, and does not certify global optimality.

## Evidence boundary

`verify_statistical.py` independently tests a full N16/U6/K10/M25 finite-Rician
fixture: full-rank moments, exact QT tightness, global lower bounds at 128 other
W points, analytic derivatives, and 20000 shared-G channel realizations. The
MATLAB test reads the same fixture and independently recomputes every moment
and derivative. Component evidence is not completion of the full original
figure sweeps, not original-code recovery, and not final-publisher certification.

The fresh source-bound spectral statistical bank actually completed all 18
configured U1..6 / satellite-Rician0,10,20dB cases and all 54 NoRIS/two-stage/AO
designs in 934.0932s. Every scheme reached its original stopping criteria and
passed independent physical, primal and QT-bound checks, with 1000 fresh
finite-Rician moment-validation draws per design. All executed source hashes
were unchanged and separately matched current files. This completes these
configured statistical sweeps only: historical-coordinate recovery,
publisher-version conformance, original-curve agreement and the distinct
instantaneous-channel figures remain separately unverified.

Subsequent source-distance audit found a confirmed reconstruction error in
that historical bank: the old15m-radius user polygon violates the original
10..20m pair-distance contract. Its true internal algorithm passes are
preserved, but it cannot certify the original scenario. This is an
implementation defect, not another author-theory erratum. The isolated
source-compliant geometry runners and distinct batches are documented in
`GEOMETRY_CONTRACT.md`; previous numerical receipts are never relabelled or
mixed with the new version. Correct mathematical identities and complete
execution alone also do not establish agreement with original EPS ordinates.
