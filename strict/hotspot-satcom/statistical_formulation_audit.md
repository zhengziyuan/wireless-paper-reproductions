# Statistical-CSI source audit: unresolved original algorithm

This is an independent algebraic audit of the supplied author-thesis Chapter3,
not a claim about the final IEEE TWC equations. The original manuscript and EPS
are not distributed. No instantaneous, LoS-only or SCA replacement is selected.

## What is uniquely implied by the stated covariance

The source states `Psi_k = mu/(1+beta) * (I + beta*h*h^H)` and iid unit-variance
NLoS samples. With `q_j = w_j^H Psi_k w_j`, its statistical QoS constraint is

`q_k >= tau * (sum_{j != k} q_j + sigma^2)`.

For the full-user-interference interpretation this is exactly

`||w_k||^2 + beta*|h^H w_k|^2 >= tau *
 (sum_{j != k} [||w_j||^2 + beta*|h^H w_j|^2] + (1+beta)*sigma^2/mu)`.

Moving the desired-stream terms into a full-J sum produces

`beta*(1+1/tau)*|h^H w_k|^2 >=
 sum_j [||w_j||^2 + beta*|h^H w_j|^2]
 -(1+1/tau)*||w_k||^2 + (1+beta)*sigma^2/mu`.

The negative desired NLoS quadratic is real. Multiplying that vector by `i`
inside an ordinary Hermitian norm does **not** subtract it: `||i*w||^2=||w||^2`.
Further, a `ones(N)^T*w` block yields `|sum(w)|^2`, not the required `||w||^2`.
Replacing `norm^2 <= linear` with `norm <= linear` fixes a dimensional-looking
typo but does not repair either of these mathematical differences.

## Nonconvexity survives the usual scalar phase fix

A finite-Rician counterexample has N=2, `Psi=diag(2,1)`, one desired stream,
unit noise and target1. Let `h=[1,0]^T`, `epsilon=0.1`, and
`w_plus=[epsilon, sqrt(1-2*epsilon^2)]^T`,
`w_minus=[epsilon,-sqrt(1-2*epsilon^2)]^T`.
Both have `w^H Psi w=1`, power0.99, and the SAME positive real LoS projection
`h^H w=0.1`. Their midpoint has `w^H Psi w=0.02` and violates QoS. Hence the
covariance-QoS feasible region is nonconvex even after fixing the LoS phase.
Changing the target to the statistical table's -3dB does not remove this
counterexample: scale the second coordinate to satisfy that positive target.

## Source-version questions that cannot be uniquely chosen by debugging

- Eq3-41b uses the NHU-only set K; Eq3-46's construction uses full J.
- The table distinguishes a statistical **LoS** NHU threshold-3dB, but Eq3-41b
  explicitly includes the full-rank `Psi_k`. A LoS-desired-power constraint
  would be a different physical/QoS model, not an algebraic fix of Eq3-41b.
- The statistical two-stage `E[A A^H]` expansion drops the random normalized
  NHU-projector denominators present in A. The source does not declare the
  denominator approximation needed to recover its displayed expression.
- Eq3-48's ratio as printed lacks the additive noise in both numerator and
  denominator when B/C are formed from the displayed Eq3-49 terms.

The noise omission can be repaired uniquely from `log2(1+SINR)`; the active
QoS convexification and normalized-projector treatment cannot. Author code,
another authoritative manuscript version, or an explicit original derivation
is needed to identify which algorithm actually generated statistical Figure3-10.
Implementing a new MM/SCA or covariance-SDP design would be a new method and is
not presented as a reproduction of the author's reported SOCP algorithm.
