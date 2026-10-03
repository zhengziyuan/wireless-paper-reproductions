# Completed-snapshot dual-language audit

This is an independent audit of every completed Python record at one frozen
snapshot, paired with its actual MATLAB-full-v2 output. It is not a smaller
production experiment, not a full-200 dual-language receipt, and not a claim
that the published Figure 3 has been recovered. The complete Python bank
continues unchanged; the separate [full-200 MATLAB evidence](../two-timescale-ma-full200-matlab-v2/README.md)
does not substitute for unfinished Python cases.

The snapshot is selected only by the runner's completion ledger. All its
records, including any failure, are retained. Input bytes and both raw outputs
are hashed before the audit and checked again afterwards. There is no
selection by rate, closest local solution, or historical figure endpoint.

The external evaluator imports no production numerical module. Its previously
frozen physical/QT/waterfill and independent concave-minorant certificate
helpers are bound by their SHA-256 identities. For each language it checks:

- the common full-size input: N=6, M=5, all 1000 exported NLoS draws;
- every saved design position, ordered coordinate objective, spacing and box
  constraint, and the actual final 5e-5 fractional-increase source stop;
- every original concave coordinate subproblem's tangent-plane global-gap
  certificate, without interpreting it as a global nonconvex AO certificate;
- all 1000 terminal sample rates, powers and applicable benchmark stopping
  gates for each of the five schemes, recomputed at that language's own
  physical positions;
- the first snapshot case's three fixed-array baselines against the independent
  per-realization scalar QT/waterfill oracle on all 1000 draws before promoting
  the batch evaluator.

The fixed sample-rate validation/comparison tolerance is 1e-7; the saved mean,
design-objective and position-comparison tolerances are 1e-9. These are the same
independent physical-audit gates used previously, not fitted to a mismatch.
The configured 100 geometries and 1000 draws and numerical benchmark controls
are disclosed reconstruction choices; the source does not report its author
Monte Carlo counts or these implementation controls.

Differences are kept in three separate categories: input identities, metric
evaluation at each saved state, and optimization state/trajectory. Even when
each language passes its own physics and source stopping gates, a differing
local state or path remains a reported difference. No offset, reweighting,
nearest-solution selection, or tolerance relaxation is applied. Enumeration
counts and MATLAB empty-array versus Python null bookkeeping are not required
to be bitwise equal.

The script is [audit_partial_dual_v1.py](audit_partial_dual_v1.py). The actual
[88-case receipt](partial-dual-completed-snapshot-v1.json) completed with 88/88
independent validation passes, no missing snapshot case, and unchanged source,
input and both-language raw hashes. The separate [summary](summary.json) keeps
the unfitted error maxima and the input/evaluator/solver-state categories. No
case exceeds the predeclared comparison gates; these are numerical agreement
checks, not bitwise equality or a guarantee for the unfinished population.

There are 880000 checked terminal sample values across both languages, five
schemes and88 cases. Byte-identical fixed-array physical states share the same
independent evaluation only within a pair; both saved 1000-sample outputs are
still independently checked against it. No samples are removed or regenerated.
All source AO stops and original coordinate certificates also pass. Any failure
would have remained in the receipt, rather than being selected out.

Run `python verify_package.py` to check the published file hashes, bound frozen
snapshot, full-size sample counts, actual stop gates and explicit partial scope.
This verifier does not rerun the private raw channel bank or promote the88-case
receipt into a full200 dual-language or historical-curve result.
