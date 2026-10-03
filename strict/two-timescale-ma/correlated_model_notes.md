# Correlated-channel interpretation and optional derivative verification

Primary source: [author-matched arXiv v2](https://arxiv.org/html/2410.05912v2),
Section V, (68)–(75), and Simulation Results, Figs.13–16. The title/DOI identity
is [10.1109/TCOMM.2025.3585515](https://doi.org/10.1109/TCOMM.2025.3585515).
The title-matched author R2 text has also been checked; it is not bundled here.

## What the model-comparison figures actually specify

Section V extends **rate analysis** and ends by explaining that rates accounting
for correlation are evaluated against the iid simplification. It does not give
a new position optimizer. The Figs.13/15 captions say “rate evaluation” for MRT;
the Fig.13 discussion describes the evolution of rates for two NLoS models.
The Figs.14/16 captions and discussion similarly concern ZF model evaluation.
Neither the captions nor the original EPS legends establish that two different
position trajectories were independently optimized.

Thus evaluating (68)/(69) and iid rates on the original Algorithm 1 trajectory
is a **source-supported interpretation for MRT Figs.13/15**. It is not recovery
of the author's original random bank, exact experimental protocol, or a verified
match to the original numerical curves. The production Algorithm 1 and its
iid curvature (29)–(31) remain unchanged. Complete Monte Carlo histories and
the (69) history are exported separately, not conflated.

## A dimension-only repair cannot establish correlated-ZF (71)–(75)

Equation (68)/(70) uses an N×N row covariance S, while (72)/(74) multiply S
with M×M factors. Those products are undefined for the published N≠M settings.
There is also a distributional issue, independently of that dimension mismatch.
Set kappa=0 and ignore scalar path-loss factors, so H=S^(1/2)U and
G=H^H H=U^H S U, with independent circular-Gaussian columns of U. Direct Gaussian
second moments give

    E[G] = tr(S) I_M,
    E[tr(G^2)] = M tr(S)^2 + M^2 tr(S^2).

For a unit-diagonal Bessel covariance, tr(S)=N. A standard central complex
Wishart W_M(N,I_M) has the same first moment, but

    E[tr(G^2)] = M N^2 + M^2 N.

When S≠I, tr(S^2)>N and the second moments differ. Replacing S by an M×M identity,
a trace-scaled identity, or another unspecified effective covariance therefore
does not preserve the stated channel law. This note does **not** propose an
alternate Wishart approximation, a replacement ZF bound, or a new optimizer.
The valid correlated channel (68) can still be simulated, but ZF Figs.14/16
cannot close the full analytical source scope without a justified formulation.

## Optional genuine derivatives of MRT (69)

These derivatives/tests are diagnostics, not production optimizer updates. Let
one moving antenna have coordinate x=t_n, all other coordinates fixed, wave
number k=2*pi/lambda, and user direction d_m. Put r_j=x-t_j, s_j=J0(k||r_j||),
a_m=k*d_m and phi_mj=a_m^T*r_j. For nonzero r_j,

    grad(s_j) = -k J1(k||r_j||) r_j/||r_j||,
    Hess(s_j) = -k^2 J1'(k||r_j||) rhat_j rhat_j^T
                - k J1(k||r_j||)/||r_j|| (I-rhat_j rhat_j^T).

Here J1'=(J0-J2)/2. At r_j=0 the removable limit is grad(s_j)=0 and
Hess(s_j)=-(k^2/2)I; no arbitrary epsilon replaces the mathematical limit.
Define q_m=hbar_m^H S hbar_m, T=tr(S^2), and
G_mj=|hbar_m^H hbar_j|^2. Their x-dependent terms are

    q_m = constant + 2 sum_j s_j cos(phi_mj),
    T   = constant + 2 sum_j s_j^2,
    G_mj = constant + 2 sum_l cos(k(d_m-d_j)^T(x-t_l)).

Thus grad(q_m)=2 sum_j[grad(s_j) cos(phi_mj)-s_j sin(phi_mj)a_m], and

    Hess(q_m) = 2 sum_j[Hess(s_j) cos(phi_mj)
                 -(grad(s_j)a_m^T+a_m grad(s_j)^T)sin(phi_mj)
                 -s_j cos(phi_mj)a_m a_m^T],
    grad(T) = 4 sum_j s_j grad(s_j),
    Hess(T) = 4 sum_j[grad(s_j)grad(s_j)^T+s_j Hess(s_j)].

The derivatives of G_mj follow by differentiating its cosine terms. Assemble
the exact numerator A_m and denominator D_m of (69), including the position-
dependent numerator. The rate derivatives are

    grad(R_m) = [grad(D_m+A_m)/(D_m+A_m)-grad(D_m)/D_m]/ln(2),
    Hess(R_m) = [Hess(D_m+A_m)/(D_m+A_m)
                 -grad(D_m+A_m)grad(D_m+A_m)^T/(D_m+A_m)^2
                 -Hess(D_m)/D_m+grad(D_m)grad(D_m)^T/D_m^2]/ln(2).

The iid denominator-only gradient/curvature cannot simply be reused, since
both q_m and T also change the numerator of (69).

## A verifiable, conservative global coordinate curvature

The integral representation J0(k||r||)=E_omega exp(i*k*omega^T*r), with omega
uniform on the unit circle, proves the following bounds everywhere, including
coincident positions:

    ||grad(q_m)|| <= 2(N-1) k(1+||d_m||),
    ||Hess(q_m)|| <= 2(N-1) k^2(1+||d_m||)^2,
    ||grad(T)|| <= 4(N-1)k,  ||Hess(T)|| <= 8(N-1)k^2,
    ||grad(G_mj)|| <= 2(N-1)k||d_m-d_j||,
    ||Hess(G_mj)|| <= 2(N-1)k^2||d_m-d_j||^2.

For q_m the Fourier frequencies are k(omega±d_m); for T they are
k(omega+nu). Multiplying the positive coefficients in (69) by these bounds
gives g_A,m, h_A,m, g_D,m, h_D,m. Since S is positive semidefinite,
A_m>=amin_m=beta_m^2*N^2. Every interference term is an expected nonnegative
squared magnitude, so D_m>=dmin_m=(noise_m/P)*N*sum(beta)>0. A triangle bound on
the exact rate Hessian yields the global Lipschitz curvature

    L_m = [(h_D,m+h_A,m)/(dmin_m+amin_m)
           +(g_D,m+g_A,m)^2/(dmin_m+amin_m)^2
           +h_D,m/dmin_m+g_D,m^2/dmin_m^2]/ln(2), L=sum_m L_m.

Consequently R(x)>=R(x0)+grad(R(x0))^T(x-x0)-(L/2)||x-x0||^2 globally.
This proves a valid same-architecture AO/SCA minorant if an optional correlated
optimizer is later implemented, but it may be very conservative. It is a newly
derived bound, **not a paper-printed algorithm**, and is not substituted into
Algorithm 1. `test_correlated_derivatives.py` checks gradient/Hessian differences,
the coincident limit, the bound/minorant on deterministic test points, and the
Wishart second-moment counterexample. Finite checks support implementation;
the integral/Hessian inequalities above provide the actual global proof.

```text
python test_correlated_derivatives.py --output correlated-derivative-test.json
```

This command runs bounded mathematical component tests, not an original MC
figure, optimization trajectory, or exhaustive search.
