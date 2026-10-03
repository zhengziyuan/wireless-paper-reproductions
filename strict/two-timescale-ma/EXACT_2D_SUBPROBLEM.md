# Same original convex subproblem, certified two-dimensional backend

The antenna coordinate is two real variables in the paper's P2.n/P5.n.
`certified_exact_2d` changes only the numerical convex-solver backend. The
MRT AO/SCA and ZF AO/MM/SCA formulas, accepted-sweep order, movement box,
original linearized spacing inequality and outer fractional stop are unchanged.

## Complete candidate set

Displacement `d=x-t_n` belongs to the bounded polygon `P={d:A d<=b}`.
The spacing row is exactly `-2(t_n-t_v)^T d<=||t_n-t_v||^2-d_min^2`, not
a nonlinear-distance projection. All pairwise boundary intersections that
satisfy **all** inequalities are retained as vertices. Every individual edge
is clipped against **all** rows, including both coordinate bounds and spacing.

MRT's unchanged minorant is `F(d)=g^T d-q||d||^2/2`, `q>=0`. Candidates
are the feasible unconstrained maximizer `g/q`, the exact maximum on every
edge, and all vertices. For `q=0`, linear/constant maxima are covered by
vertices and feasible zero displacement: PSD-singular/flat cases are not ridged.

ZF's unchanged minorant, up to a constant, is
`F(d)=sum_m log2(r_m(d)/r_m(0))`,
`r_m(d)=a_m+g_m^T d-q_m||d||^2/2`,
`a_m=chi_m+f_m(0)+1/eta_m=ratio_m+1/eta_m>0`.
Using the paper's exact tangency identity `chi+f0=ratio` avoids cancellation
without altering coefficients. The positive-log domain is convex; on its
finite boundary the objective tends to minus infinity. Thus a finite maximum
is interior to the polygon, on a polygon edge, or a finite-domain vertex.
Analytic-gradient/Hessian Newton finds interior stationary candidates. Every
edge's complete positive-log interval follows from all quadratic/linear
domain inequalities; monotone derivative signs and scalar roots locate its
maximum. This solves the original convex program, not a replacement outer
projected-gradient update. A missed/inaccurate candidate fails the certificate.

## Independent global certificate

Concavity gives `F(y)<=F(d)+grad F(d)^T(y-d)` for every finite-domain feasible
`y`. Therefore `F*−F(d)<=max_vertex grad F(d)^T(vertex−d)`.
Domain-invalid vertices are used only for this **linear** upper bound; their
logarithms are never evaluated for certification. The polygon contains the
positive-log feasible domain, making this bound conservative.

The disclosed numerical objective-gap tolerance is
`max(1e-10,1e-10*abs(original objective))`; normalized primal tolerance is
`2e-12*max(1,max(abs(normalized b)))`. Every bound/residual must be finite
and pass. These are numerical certificates, not interval-arithmetic formal
proofs, and imply no global optimum for the nonconvex outer antenna design.
No original outer stopping inequality is relaxed. Both language resume gates
require every stored coordinate certificate. Conic `optimal_inaccurate` and
`user_limit` flags are not relabeled as convergence. Optional explicitly
selected CLARABEL/CVX branches remain available for the same convex program.

## Actual tests and historical receipts

Python original-objective identities, independent ZF gradient/Hessian
differences, all twelve full-N6/M5 coordinate calls, linear/flat MRT,
infeasible coincident-antenna rejection, and two actual failed-coordinate
regression fixtures have passed. A previously failing full geometry executed
both original algorithms, all five benchmarks and all1000 NLoS samples.
This is not a complete100-geometry figure or an original-curve match.

Old conic-bank failures are retained. Formal exact-backend runs use a new
immutable bank name, configuration snapshot and implementation fingerprint,
while retaining100 geometries and1000 NLoS draws per geometry.
