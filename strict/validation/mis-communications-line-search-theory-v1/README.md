# MIS communications: exact source-theory limits

This audit marks issues in the supplied R2 author source, SHA256
`6e27fb9fd2ba0decc9d7bcfc54bcb73612553f91f6df923ab502e7d561058cb0`.
It is not an official publisher erratum, a new scientific campaign, a substitute
algorithm, or a diagnosis of the current full Figure11 failures. The private
manuscript is not redistributed. Both full-scene implementations and their
budgets remain unchanged by this audit.

## Printed raw PR is not necessarily a descent direction

The R2 projection, PR, transported direction and circle retraction are at
source lines507/542/546/578. They do not, without additional conditions,
guarantee a descent direction even following an Armijo-accepted step.

The analysis uses the mathematically consistent minimization cost F=-f,
negating both the maximized softmin and its gradient. The source's maximized
f versus printed minus-gradient/minimization sign conflict is already disclosed
in [COMM_ERRATA.md](../../mis-communications/COMM_ERRATA.md). This audit tests
the unchanged raw PR/transport/retraction formulas under that explicit sign
convention, not an unnoticed change of the objective or a new solver.

Use the legitimate physical SMS specialization M64, K1, c=ones64, X=1 and
iota=169/10240. This deliberately declared theorem witness is not Figure11's
K2:2:16 grid or its iota0.01. At K1 the minimized negative softmin is exactly
F=-iota*|sum(phi)|^2, for any smoothing parameter. Start with32 phases
z0=(12+5i)/13 and32 conjugates. The projected gradient coefficient is3/4.
The original minus-gradient step of size1 and normalization gives
z1=(63-16i)/65 and an exact objective decrease of-738/125. This meets both
the ordinary and displaced Armijo tests with constant1/10000.

At the new point the gradient coefficient is-63/125, the transported old
direction is-3/5, and the printed PR coefficient is15456/15625. The next
direction coefficient is-6993/78125. Its real metric slope over64 phases is
28195776/9765625 >0: ascent for minimization. For every0<alpha<=1,
the retracted real part remains positive but decreases, so the original
objective increases. Backtracking alone cannot repair this direction.

The same example lifts to a true MIS model: M1x64, N1x1, U64, K1,
theta=1 and every X entry1/64, strictly inside the reported positive simplex.
All shifted beams have the same field; X's row-projected gradient is zero,
theta's circle-projected gradient is zero, and phi's update is exactly the
one above. This is a source-theory example, not a smaller replacement scene.

The current reconstruction already restarts non-descent directions. Therefore
this witness does **not** prove the cause of its remaining line-search failures,
nor that a selected simulation result is invalid. Literal formula behavior and
disclosed safeguards must remain distinguishable.

## Stationarity is not local optimality; simplex scope matters

R2 line640 infers local optimality from stationarity. At32 phases+1 and32
phases-1, the field and all gradients vanish. Perturbing one phase by any
sufficiently small nonzero angle produces |exp(it)-1|^2>0, improving SNR.
Thus stationarity alone does not imply a local SNR maximum. This also lifts
to the MIS specialization above; no observed campaign state is asserted.

The strict-positive simplex in R2 lines398/410 is not compact for U>1.
The stated closed-simplex projection can return boundary zeros: projecting
(1/2,1/2)+(1,-1) gives(1,0). The appendix's explicit projection description
is in a TeX comment, which is not active manuscript text. Existing boundary
KKT corrections remain disclosed; no zero is relabelled as convergence.

## Runnable controls and limits of the evidence

From the repository root, with ordinary Python and no third-party libraries:

```sh
python -B strict/validation/mis-communications-line-search-theory-v1/verify_theory.py
```

The ten controls cover the exact physical gradient/normalization, accepted
previous step, PR/transport signs, stationarity counterexample, open-versus-
closed simplex, exact field-increment identity, MIS lift, and three explicitly
synthetic binary64/backtracking bookkeeping mechanisms. Synthetic mechanisms
are not observed failure causes or numerical accuracy certificates.

ROOT actually ran all nine local source-audit controls and all ten portable
controls successfully on5 October2026. The independent local nine-control
receipt SHA256 is
`9fa66eefcb146d025cdfe552c2906b76339efcc32eddee3728a010fc06dfe9fa`.
The portable checks are not claimed BYTE-identical to that source: explanatory
comments/formatting and the additional exact MIS-lift control differ.

Current full producers already use a stable objective increment at every mu.
No new sign, transpose, or phase-gradient implementation error was established
by this review. Actual rejected trial states, gradients and Armijo margins are
not fully retained in the existing histories; their historical values cannot
be manufactured from endpoint summaries. Remaining failures, convergence,
dual-language complete coverage and unfitted reference agreement still need
genuine full-scene evidence. No threshold, winner, curve, budget or solver is
changed here, and the whole six-paper reproduction remains incomplete.
