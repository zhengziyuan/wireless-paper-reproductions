# MA Fig3/4 original-source / actual-input audit

Scope: read-only author-R2 source lineage, current Python and native MATLAB
model/normalization bodies, all200 immutable exported inputs, and independent
reconstruction of Eq13/Eq37 at each original initial geometry. No optimizer,
new full Monte Carlo rate evaluator, historical-figure vector publication,
model change, reference fitting, or gain/noise tuning is performed.

The two accessible title-matched author `bare_jrnl.tex` copies are byte identical
SHA256 `9ba173a0da8fcd472bb211155e0a4c1e7b9a0104a718bd88ac166808be876b19`.
This establishes supplied-author source lineage, **not** independently obtained
final IEEE publisher conformance. Source anchors are in the actual receipt.

## Confirmed Fig3/4 model and units checks

1. Source Eq1/2 lines127–139 gives unit-amplitude LoS steering elements and
   `h=sqrt(beta*kappa/(1+kappa))*hbar+sqrt(beta/(1+kappa))*z`.
   Both implementations use this formula without an additional `1/sqrt(N)`;
   `norm(hbar_m)^2=N`. They use exactly the source direction vector
   `[cos(theta)*sin(phi),sin(theta)]` and positive steering exponent.
2. Numerical paragraph lines869–871 defines beta as a **power** gain:
   `beta=10^(-40/10)*d_m^(-2.8)`, distances in metres, noise−80dBm=
   `10^((-80-30)/10)=1e-11 W`, P1 W, A2, N6/M5, kappa6/100 **linear**.
   These match current Python/MATLAB and every actual exported case. No squared
   beta gain, missing dBm−30 conversion, amplitude-vs-power confusion, extra
   feed count, or 16-stream satellite-package contamination was found here.
3. Source MRT lines213–229 uses the common coefficient
   `p=P/sum_m(norm(h_m)^2)`, not equal per-user normalized beams. Both current
   implementations use `W=H*sqrt(P/sum(abs(H)^2))` with total instantaneous
   beam power P. Source ZF lines493–513 uses normalized projection columns and
   power P/M per stream; both implementations use normalized pseudoinverse
   columns and P/M. The Gram inverse/SINR orientation is `H^H W`, not `H^T W`.
4. Wavelength1 is an exact choice of normalized antenna-position units:
   `t_physical=lambda*t_normalized` cancels lambda from the phase. User distances
   in the path loss remain in metres. The source's unrelated12GHz motor-energy
   footnote does not mandate scaling beta or noise in the rate figures.
5. All200 actual jobs have NLoS arrays1000×6×5, finite distances50..70m and
   angles−pi/2..pi/2. The complete geometry and all1000 Gaussian vectors are
   identical between the kappa6/100 partner jobs for each of100 realization IDs.
   Both algorithms in `run_job` consume that same job; neither receives a
   different user order or NLoS ensemble. The actual source-lineage receipt
   rebuilds both initial formulas independently. Maximum source formula
   differences: MRT3.5527e-15 and ZF9.2371e-14 bps/Hz. This verifies these
   specified inputs/formulas, not all possible implementation defects.
6. Unlike the satellite model, this source supplies the entire per-antenna LoS
   steering law. There is no evidence of an omitted random per-feed deterministic
   mean phase. A global per-user reference phase is not an extra physical gain:
   it leaves the source statistical Gram/objectives invariant (and expected
   rates invariant under circular Gaussian rephasing). It cannot justify
   arbitrary independent phase/gain tuning to the reference curves.

## Classified source issues versus missing historical input

- **Confirmed source mathematical/type issues already explicitly handled**:
  Eq29b's negative discriminant conflicts with Eq29a's real symmetric maximum
  eigenvalue; Algorithm2 has erroneous problem/spacing cross-references. Current
  declared repairs use Eq29a and the actual stated spacing/program. They are not
  evidence that the remaining reference gap is caused by a power-unit mistake.
- **Source errors outside iid Fig3/4**: the initial correlated prose writes
  `S*u` while defining S as covariance (later Eq68 writes `sqrt(S)*u`); for iid
  S=I both coincide. Correlated-ZF dimensions and the12GHz motor-energy footnote
  have separate errata and cannot automatically explain iid Fig3/4 differences.
- **Unreported historical inputs**: N_r/N_c, exact initial antenna positions,
  sampled user distances/angles and their joint dependence, Gaussian vectors,
  MC/geometry counts/seed, and whether the convergence curve is one geometry or
  an average across random user geometries. Source Algorithm1/2 merely says to
  initialize t_n^0; numerical text specifies marginal uniform distributions,
  not stored individual draws or a unique joint realization. Current100
  geometries/1000 vectors, independent marginal draws, centered half-wavelength
  lattice and N_r2/N_c3 are declared reconstruction choices.
- **No unique causal conclusion**: no confirmed Fig3/4 link-budget, LoS
  normalization, stream-count or same-vector input conflict was found in the
  inspected chain. It is equally unjustified to call all remaining difference
  a paper error or to attribute roughly4bps to the seed. Historical initial
  geometry and averaging protocol can affect the nonconvex trajectory, but the
  available evidence does not identify which one generated the original figure.

There is a concrete reason not to reduce the missing factorization to merely a
seed detail: under the currently declared independent uniform theta/phi law,
`E[a_x^2]=E[cos^2(theta)]E[sin^2(phi)]=1/4`, whereas
`E[a_y^2]=E[sin^2(theta)]=1/2` and `E[a_x*a_y]=0`. Thus the direction distribution
is anisotropic; swapping a2-by-3 and3-by-2 array/rectangle is not generally a
distribution-preserving rotation. The companion exact-arithmetic witness proves
this fact and a deterministic global-reference-translation phase identity.
It does not choose a better factorization, fit any curve, or claim that this
caused the historical gap. Both Nr/Nc and the joint angular sampling convention
are missing historical-input information that can matter beyond seed noise.

The opening system description calls the region square A-by-A (line123), while
the explicit numerical paragraph specifies an NrA-by-NcA rectangle (line871).
Current figures adopt the explicit numerical-region rule; this disclosed
source-scope difference is not an implementation violation of that numerical
rule, and no square-region rerun is substituted.

The current original-figure disagreement remains real and unresolved. A true
full computation of the disclosed reconstruction is distinct from historical
curve recovery. This audit does not change any live source/result or upgrade
existing false historical-figure flags.
