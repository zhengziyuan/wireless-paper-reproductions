# Exact raw-PR theory-scope counterexample — not a reduced simulation

The title-matched supplied R1 manuscript (SHA256
`aa71da008c68caa605ec3ed17520fcb81796561f315667eeb2f7dddf1487d2d2`)
uses untruncated Polak–Ribiere, tangent projection, projected-vector transport,
element-normalizing retraction and Armijo in source lines705–773. Lines738–747
call the direction ascent; line776 states a stationarity guarantee without
conditions ensuring sufficiently ascending, gradient-related directions.
The matching accessible mathematical source is the
[revised arXiv full text](https://arxiv.org/html/2512.20987v2).
Final IEEE-version equivalence has not been established.

This portable test uses **exact integers and rational inequalities**, without
NumPy, an optimizer, channels, RNG or MATLAB. It is a mathematical negative
control of the printed direction formula, not a smaller physical reproduction.

One source sensing amplitude `1+conj(theta)`, `pd=1`, `iota=2`, `rho=1` and
zero communication power give the original negative NMSE objective
`F=-Re(theta)^2` on the unit circle. Start with
`theta0=(1+10i)/sqrt(101)` and the source quartic ambient gradient. The first
printed tangent direction, initial step1, normalization and Armijo c=1e-4 give:

- `theta1=(-99+1030i)/sqrt(1070701)`;
- exact gain `800/1070701 > 1/255025`, the original Armijo requirement;
- next phase gradient `a1=-203940/1070701` and transported old gradient
  `20/sqrt(10601)`, retaining the **old** norm denominator;
- next raw-PR slope strictly below
  `-399237035036400/12152993093482001 < 0`, proved using
  `10601 < 103^2`, with no rounded square-root or sign decision.

Thus raw PR alone does not guarantee an ascent direction after an accepted
Armijo step. A stationarity theorem requires additional direction/line-search
assumptions or an explicitly identified safeguard. This does **not** disprove
conditional convergence results or show that the author's historical channels
realize this component. No PR+ clipping or restart is silently introduced.

The reconstruction already separately labels its non-ascent restart mode;
literal mode must retain the failure. Another actual failure at iteration4614
has a **positive** slope and a numerical unit-state representation problem:
the present negative control must not be used to classify that point as
non-ascent or converged. The full-scene failures and original stopping threshold
remain unchanged.

The same real-coordinate representation preserves the printed algebra:
`theta=exp(i*phi)`, `g=i*theta*a`, `d=i*theta*b`, transport
`a_old*cos(phi_old-phi)`, and retraction `phi+atan(alpha*b)`.
Replacing the last expression by `phi+alpha*b` would change the method.
The tests separately retain transport contraction, negative raw beta and a
normalization-retraction identity. They do not certify a numerical provider,
new cold trajectory, full six schemes or a figure.

From the repository root:

```text
python strict/validation/rotatable-isac-raw-pr-scope-v1/test_exact_raw_pr.py --output strict/outputs/raw-pr-scope/actual-exact-component.json
```

Use a fresh output path. Six exact tests pass locally; CI invocation only
checks these components, never the original scene population.
