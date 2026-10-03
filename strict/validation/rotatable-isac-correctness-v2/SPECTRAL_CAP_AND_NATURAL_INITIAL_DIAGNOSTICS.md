# Declared INITIAL-trial diagnostics: all outcomes, no promotion

The article reports an Armijo INITIAL-trial symbol but not the numeric seed or
RCG iteration cap. These component diagnostics change only those explicitly
unreported reconstruction controls, alongside previously checked arithmetic
for the same original utility difference. Raw PR, original tangent transport,
direction, literal normalization retraction, original Armijo inequality,
backtracking and gradient tolerance remain. All cases use full M4/N36/K2/A66.
They are first cold RCG blocks, not six-scheme complete scenarios or full banks.

The independently declared BB1/BB2 seeds at the fixed10000 diagnostic cap give:

| INITIAL control | Input | Actual iterations | Original normalized gradient | Original1e-6 stop |
| --- | --- | ---: | ---: | --- |
| BB1 | case001 | 10000 | 0.00827392703705 | Not met |
| BB1 | case002 | 2048 | 0.000000900872339193 | Met |
| BB2 | case001 | 10000 | 0.00194175351017 | Not met |
| BB2 | case002 | 10000 | 0.00131161427089 | Not met |

All four retain bitwise equality to their own previously declared500-update
prefix, including objectives, PR/restarts, seed/accepted-increment records,
post500 phase state and cold W history. Cap bookkeeping is excluded explicitly.
Fixed MP50/80 original-utility Armijo/secant checks and all36 endpoint MP50
finite-difference gradient checks pass; they are numerical checks, not formal
interval proofs or evidence that every10000 update was checked at MP80.

The read-only complete data inspection found scalar-ceiling1 clipping of
113/9995,178/2046,9/9306,138/9923 valid seeds respectively. This numerical fact
motivated, but did not prove success of, a separately declared natural INITIAL
trial. It alternates BB1/BB2 by update parity, sets U=1/max|original direction|,
uses U as its fixed fallback, and clips a valid positive seed to[2^-1022,U]. For
an exact unit-circle tangent, the INITIAL coordinate phase increment is at most
atan(1)=pi/4. The displacement is utility-scale covariant when the numerical
floor is inactive. Neither statement is a convergence theorem.

Both natural-control cold500 blocks returned but **did not meet** the original
gradient stop: case0010.0206464362192 and case0020.0194184019912. Their fixed
MP50/80 Armijo/increment/seed and all36 endpoint gradient checks pass. This is
a different INITIAL rule, so no old-prefix equality is claimed. Both failures
are preserved; removing the scalar ceiling is not established as a remedy.

The compact JSON receipts include all declared outcomes and pre-result source
hashes; large states remain in retained WORK raw files whose hashes are recorded.
No favorable case is selected as a replacement algorithm. No failed original
controls or flags are overwritten, no live bank is changed, and no production,
MATLAB parity, complete original figure, or all500-input success is claimed.
