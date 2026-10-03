# Fixed four cold spectral-INITIAL diagnostics, cap 100000

These are all four predeclared full-dimensional M4/N36/K2/A66 cold **first RCG
blocks**, not a selection of successful branches, six-scheme complete scenarios,
or the 500-input bank. The manuscript leaves the numeric INITIAL Armijo trial
and this RCG safety cap unreported. This WORK experiment extends the unchanged
BB1/BB2 scalar-ceiling-one controls from the previously declared cap 10000 to
100000. It does not use the separately tested natural alternating control.

| Declared INITIAL control | Fixed input | Actual iterations | Final normalized gradient | Original implemented 1e-6 stop |
| --- | --- | ---: | ---: | --- |
| BB1 | case001 | 81732 | 7.315247010535248e-7 | Met |
| BB1 | case002 | 2048 | 9.008723391934559e-7 | Met |
| BB2 | case001 | 100000 | 1.6463678316404304e-4 | **Not met: retained cap** |
| BB2 | case002 | 30555 | 9.923370642534066e-7 | Met |

The serial single-worker experiment completed in 856.81 seconds. All four
cold runs retain bitwise equality to every available update of their own
previous 10000-budget run: objective histories, raw PR coefficients/restarts,
INITIAL seed and accepted-increment records, phase state at the old endpoint,
and the original cold W history. Case002/BB1 had already stopped at 2048;
its entire available prefix is checked without inventing 10000 updates.

The original raw PR, transport, search direction, documented non-ascent
restart, literal retraction, Armijo inequality, backtracking, W update,
physical model and gradient threshold remain unchanged. The previously
independently checked increment arithmetic evaluates the **same** utility;
neither Wolfe nor a preconditioner, a changed objective, a relaxed threshold,
or an alternative stopping rule is introduced.

All four pass the fixed original-physical-utility MP50/80 Armijo, increment
and spectral-secant checkpoints (when reached) and the independent scalar
MP50 centered-difference check of all 36 endpoint phase gradients. These
finite numerical witnesses are not interval certificates, checks of every
100000 update at MP80, a convergence theorem, or independent MATLAB parity.
The exact predeclared checkpoint identities and unchanged precision gates
are bound by the start manifest and retained WORK source hashes.

**Three stops out of four is not a complete convergence repair.** The
BB2/case001 failure, every earlier 500/10000/natural-control failure, and all
raw states remain retained. This diagnostic is not promoted into the frozen
production package or used to restart/mix the live bank. It does not establish
historical figure agreement or complete-paper reproducibility.

The compact receipt binds the actual aggregate, the pre-result manifest, all
four original input/raw identities, and the unchanged source fingerprint.
The >100 MB raw histories stay in retained local WORK evidence; they are not
silently replaced by the compact publication receipt. A separate new manifest
freezes only these new diagnostic publication files and does not rewrite any
earlier evidence manifest.
