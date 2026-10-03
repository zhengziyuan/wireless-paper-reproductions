# Reported dimensions versus reconstructed numerical controls

Direct read-only audit of the matching author R1 manuscript source, SHA256
`aa71da008c68caa605ec3ed17520fcb81796561f315667eeb2f7dddf1487d2d2`.
Only source locators and findings are provided; no private TeX or author code
is redistributed.

## What the source reports

The simulation setup atL1073–1105 specifies the full physical domain: default
M4 active antennas, N36 passive elements, A66 sensing directions, two paths per
link, six benchmark families, and **100 independent channel realizations**.
These dimensions, paths, schemes and100-channel population must not be reduced.

Algorithm2 atL759–773 uses the normalized Riemannian-gradient criterion
`norm(Rgrad F)/sqrt(N) <= epsilon` or a symbolic `j_max` budget. Algorithm3 at
L981–1028 uses the component-wise box projected-gradient residual or relative
accepted-angle step, with symbolic positive tolerances and `I_PGA_max`.
Outer AO atL1046–1054 uses a symbolic relative-utility tolerance or maximum
iteration. None of these source sections assigns500,1e-6 or1e-8 to RCG/PGA
controls; a complete source search finds no such numerical assignment.

Therefore current **RCG500/PGA500, gradient1e-6 and PGA relative-step1e-8** are
declared reconstruction controls, not reported author budgets or tolerances.
The W cap10000 similarly revises an unreported safety control; it does not change
the original QT/MM update. Do not conflate these with budgets explicitly
reported in another paper, such as MIS sensing.

## What actual checks establish—and do not establish

The full-size original active case001 first RCG block reached500 without its
gradient criterion (Python final normalized gradient0.0051074 >1e-6); an
independent MATLAB active fixture also retained a500-cap failure. This is not
merely a last-step bookkeeping issue. Source Algorithm2's new-state check and
the implementation's next-loop check may affect cap-boundary flags, but cannot
turn these measured above-threshold gradients into a passed criterion.

A separate WORK-only first-PGA replay raised only the unreported cap500→10000,
from the original first-AO state. Every original500 history/BB/accepted-step
entry and all1895 state/metric/gradient evaluation records matched bitwise.
It **still did not converge**: final relative step9.9855e-8 >1e-8 and projected
residual0.32321 >1e-6. Larger budgets alone are not yet a verified remedy.
The healthy full500-case live bank and its immutable controls are unchanged.

A second fresh WORK-only RCG replay likewise changed only the unreported
cap500→10000, from the identical original initial phase state, **not a reset
from the500-step endpoint**. All original500 objectives, raw PR coefficients,
documented restarts and all7832 state/metric/gradient evaluations were an exact
bitwise prefix. It too remained capped: final normalized gradient
0.00384805755 >1e-6. Thus neither10000-step diagnostic has established a
converged remedy. These actual retained failures motivate gradient and
line-search diagnostics, not tolerance relaxation or a claim of reproduction.

The separate actual case002 failure has now been cold-reproduced at the33rd
RIS block, RCG iteration442. Independent50/80-digit evaluation of all80 original
stored trials shows that `alpha=6.103515625e-5` gives a true utility increase
`4.2978951e-14`, exceeding the unchanged Armijo requirement `1.0420514e-17`.
The original binary64 absolute-value subtraction instead reports
`-5.8797411e-13` and rejects it. This is a verified numerical rejection, not
evidence that the gradient threshold has been met. Its above-threshold gradient
and the distinct real cap failures remain recorded.

[Actual single-step precision evidence](../validation/rotatable-isac-correctness-v2/actual-case002-armijo-step-highprecision-v2.json)
also retains the first stable-increment accuracy failures and the fresh same-path
higher-precision tests that pass the **unchanged** accuracy gate. WORK-only
cold full-scheme replays retain the literal retraction, raw PR direction, original
Armijo, all dimensions and all stopping controls. Their numerical acceptance
decisions can change binary64 trajectories; they are not old-prefix bitwise
proofs, and neither a full-scheme completion nor a full500-bank success is
claimed by the single-step receipt. The live frozen numerical source is unchanged.

Any new control version must keep the complete source physical domain, preserve
old failures, use a distinct immutable configuration/identity, and re-execute
the required full population. First-block or exact-cache proofs are not a
completed six-scheme scenario, full100-channel figure, or historical curve match.
No stop tolerance is silently relaxed and no unfinished block is relabeled.
