# Exact projected-curve kink control — not a physical figure

This portable negative control identifies a limitation of **our disclosed
corrected product-PR/strong-curvature branch**, not a claim that the printed
author algorithm uses strong Wolfe. It also does not identify the cause of a
particular observed MIS iteration cap. No production code, original stopping
tolerance, direction or line-search acceptance rule is changed by this packet.

Let X0=(1,0), dX=(-1,1), eta0=0, deta=1 on the two-coordinate closed simplex
times R. Choose the smooth affine ambient function f(X,eta)=eta/2-X2.
Projection of X0+alpha*dX is (1-alpha,alpha) for 0<=alpha<=1 and (0,1) for
alpha>=1. The resulting line curve is

    phi(alpha) = -alpha/2       for 0<=alpha<=1
               = alpha/2-1     for alpha>=1.

This curve is continuous, bounded below by -1/2, and initially descending.
Every differentiable positive step has derivative -1/2 or +1/2. For the
declared c2=1/10, strong curvature would require magnitude <=1/20, so **no
differentiable positive step satisfies it**. At alpha=1 the ordinary
derivative does not exist. The current positive-support derivative convention
instead selects +1/2 there and also fails that test, although exact Armijo
with c1=1/10000 holds at that step.

The generalized derivative interval at the kink contains zero. Adopting that
set-valued criterion would be a separately declared algorithm change; this
test does not enable it. Ordinary smooth-curve Wolfe-existence arguments
therefore cannot automatically justify the current closed-projection branch.
This does not prove that all physical MIS search curves lack acceptable steps,
or that a new safeguard necessarily cures the complete original bank.

Recheck with standard-library Python only, using a fresh output name:

```text
python -B strict/validation/mis-sensing-projected-curve-kink-v1/verify_projection_kink.py --new-report my-exact-check.json
```

The included actual receipt records exact rational/integer checks and verifier
byte identity. The branch argument covers all alpha in both intervals, rather
than testing a finite step grid. MATLAB native runtime parity, physical models,
all6000 starts and original-figure recovery are not certified by this packet.
