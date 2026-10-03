# BB1/BB2 initial Armijo controls: actual fixed-four500 diagnostic

This WORK test addresses an unreported **initial trial** control, not the paper's
search direction. The [source contract audit](RCG_SOURCE_CONTRACT_AUDIT.md)
requires raw PR, projected transport, literal normalization retraction and
Armijo backtracking; it does not prescribe Wolfe. The existing documented
non-ascent restart safeguard remains explicitly distinguished from a printed
author instruction.

With the same current transport T and previous accepted alpha/direction, define
s=alpha_previous*T(d_previous) and y=T(g_previous)-g_current. The sign models
curvature of minus the maximization utility. BB1 uses Re<s,s>/Re<s,y>, and BB2
uses Re<s,y>/Re<y,y>. Each strategy separately uses a finite positive seed,
clipped to [original_initial_alpha*2^-40, original_initial_alpha], with the same
fixed original-alpha fallback on the first update or invalid secant. These are
local scalar predictions, not preconditioners, alternate directions, global
curvature bounds, line optimizers or convergence certificates.

The [predeclared manifest](spectral-BB1-BB2-full500-predeclared-manifest-v1.json)
was saved before numerical tests. The population contains all four combinations
of BB1/BB2 and the real case001/case002 cold first blocks, retaining M4/N36/K2,
all66 pattern directions, all rays, original first W update, raw PR and Armijo.
The declared500 cap and1e-6 gradient criterion are not author-reported numerical
settings. Neither is changed in this test; no best strategy is selected.

The [actual receipt](spectral-BB1-BB2-two-real-cases-full500-negative-diagnostic-v1.json)
returned all four complete500-update blocks without exceptions. **None meets
the unchanged gradient criterion.** Every failed outcome remains:

| Fixed control | Case | Actual final normalized gradient | Original stop met |
| --- | --- | ---: | --- |
| BB1 | 001 | 0.0012621111 | No |
| BB1 | 002 | 0.0579236334 | No |
| BB2 | 001 | 0.0007508940 | No |
| BB2 | 002 | 0.0212721716 | No |

All20 synthetic secant/clip reference checks at50/80 digits passed. On each
actual block, fixed update indices0/249/499 passed the original scalar physical
Armijo test and unchanged stable-increment precision gate at50/80 digits, with
the literal stored retraction and independently checked secant prediction.
Each endpoint's all36 phase-gradient components also passed independent
original-scalar MP50 central finite differences (fixed step1e-6/component
atol1e-7). The latter is a diagnostic arithmetic check, not a relaxed1e-6
optimization stop or a formal interval bound. Source and input hashes stayed
unchanged, and old constant/curvature-control failures were not overwritten.

These checks establish same-objective implementation correctness for the
declared tests; they do not establish a convergence remedy, full six-scheme
scenario, full500-channel bank, MATLAB agreement, or original-curve recovery.
No production promotion is proposed. A separately predeclared fixed10000
WORK continuation of all four controls must report its own outcomes and verify
each complete retained500 numerical prefix; it cannot change these failed flags.
