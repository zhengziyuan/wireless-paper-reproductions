# RCG source contract: no inferred Wolfe correction

Read-only audit of the matching author R1 manuscript, SHA256 `aa71da008c68caa605ec3ed17520fcb81796561f315667eeb2f7dddf1487d2d2`. The private manuscript is not redistributed. Source line locators refer to this hash, not an unspecified later version.

| Item | Source locator | Current Python/MATLAB interpretation |
| --- | --- | --- |
| Riemannian gradient | L728–734 | Orthogonal complex-circle projection of the real-objective Euclidean gradient. Independently checked against the original scalar objective. |
| PR coefficient | L738–743 | Raw untruncated PR; numerator transports the old gradient into the new tangent space, denominator is the old gradient's own squared norm. No PR+ clipping is printed. |
| Conjugate direction/transport | L744–748 | New Riemannian gradient plus raw PR times projected old direction. Real part of the complex inner product is used. |
| Retraction | L749–757 | Element-wise normalization of theta plus step times the same search direction. |
| Line search | L757, L767 | **Armijo backtracking** is explicitly named. Wolfe/strong-Wolfe is not required anywhere in the audited source. |
| Stopping | L763–770 | REPEAT update, then new-state normalized gradient threshold or symbolic maximum j. No numerical minimum-j is assigned. |

For this RCG subsection, the source does not assign numerical initial step, alpha-bar, c1/c2, backtrack ratio, maximum backtracks, epsilon, or j-max. The kappa1/kappa2 conditions at L979–981 and BB clipping at L974–976 belong to the **separate rotation PGA subsection**; they must not be silently transplanted as reported RCG settings. Current initial step 1, Armijo coefficient 1e-4, backtrack ratio 0.5, 80 backtracks, epsilon 1e-6 and cap500 are declared reconstruction controls.

The implementation's documented non-ascent restart is a safeguard extension, not an explicitly printed instruction in Algorithm2. The raw printed PR direction can genuinely be non-ascent; literal mode retains that diagnostic failure rather than secretly using PR+. Consequently the safeguarded implementation cannot be presented as uniquely recovered historical author code. Replacing Armijo with Wolfe would add a condition not prescribed in this paper; the source audit does not justify that change as an implementation correction.

The printed REPEAT/new-state stopping test differs from the implementation's pre-loop test at initialization and at the last-cap update. This is a stopping-bookkeeping distinction, not an explanation of case001's independently measured 10000-step gradient about 0.0066579. Zero-gradient initialization is already stationary; a cap-boundary state still must be evaluated against the original threshold, not relabeled by reaching a budget. No live source was changed by this audit.

## One fixed same-direction initial-step proposal

Let phi(alpha) be the **original** fixed-W/r/iota utility at the **same literal normalization retraction** along the **same raw-PR/ascent-restarted direction**. For a finite positive original slope s and finite negative phi''(0), predeclare only the initial trial as `clip(s / (-phi''(0)), original_initial_step*2^-40, original_initial_step)`; otherwise use the original initial step. Every subsequent trial keeps the original backtrack factor and original Armijo inequality. The clamp and fallback are fixed before testing, not fitted to a graph. No direction, metric, stopping threshold, phase grid, physical dimension, or cap changes.

This is a local Newton prediction of the initial trial, **not** a Hessian preconditioner, alternate line optimizer, global curvature bound, Wolfe test, or acceptance certificate. Both real failure cases must be tested with their full dimensions and original controls, and the captured case002 failed step must independently pass original physical Armijo. A previously completed case001 first500 test still failed the original gradient criterion; therefore the proposal is not an established convergence remedy and is not promoted to production. Component and real-case receipts must report failures, not just successful return values.

The fresh [two-real-case full500 preflight](same-fixed-initial-seed-two-real-cases-full500-preflight-v2.json) actually completed both original cold first blocks with the single fixed seed. Neither reaches the unchanged 1e-6 gradient gate: the final norms are 0.0624323 for case001 and 0.00121900 for case002. At the separately captured real case002 failed direction, that same predicted trial passes the original scalar Armijo and unchanged accuracy checks at 50/80 digits. This single-step result does not replace a cold replay of the entire failed block or whole scheme; the prediction is still not a verified remedy and is not promoted.
