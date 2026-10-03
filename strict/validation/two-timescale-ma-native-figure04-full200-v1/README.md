# Native Fig. 4: full200 independent physical history check

All 200 actual MATLAB trajectories (100 geometries for each kappa6/100),
N6/M5, and **all 59,813 recorded positions × 1,000 original draws** passed
the independent QR physical replay. The 59,813 positions include 200 initial
states and 59,613 post-sweep states, not 59,813 fresh optimization updates.
All sample rates, saved means, power equalities, relative ZF residuals, original
statistical design objectives, spacing/box domains and true original stopping
conditions were checked. Source/input/raw/evaluator before/after hashes match.
The first/last state of the first case also passed all1000 scalar-SVD checks.

This Fig. 4 protocol evaluates the original completed Fig. 3 ZF trajectories;
**no positions are optimized again**. Actual MC rates and the Eq. 39 statistical
design objective are separate series. The geometry and draw counts100/1000 are
declared reconstruction controls, not counts reported by the author. The
earlier all200 coordinate global-gap proof is linked through its immutable
Fig. 3 packet manifest; this packet does not claim a second coordinate audit.

The plotted average uses every100 legitimate stopped trajectory per kappa and
explicitly holds each final accepted state after completion. That is not a
fictitious update, a best-geometry selection or the recovered historical author
averaging protocol. The data retain the entire mean trajectory lengths and
held-geometry counts even though the original comparison domain ends at600.
Both fixed initial-index conventions0/1 are reported without selecting the
closest fit. Original EPS curves are not scaled, shifted vertically, reweighted
or used to tune power/noise/geometry. Original curve closeness remains **false**;
the largest unfitted absolute discrepancy is about4.79553bps/Hz. Native physical
correctness does not by itself establish recovery of the historical figure.

The separate full200 ensemble audit preserves the same100 geometries and all
1000 draws across both kappas. The final-state MC mean is28.409218/28.871340 for
kappa6/100, whereas the plotted sweep599 means are28.256229/28.326571. The author
endpoints are30.860137/32.564915. These quantities are deliberately different;
91/80 geometries have stopped within500 sweeps. An author endpoint inside the
100-geometry distribution is not evidence of a particular historical geometry
or a unique explanation; no closest geometry is selected or reweighted.

## Verify the published evidence

From the repository root, with NumPy/SciPy installed:

```text
python strict/validation/two-timescale-ma-native-figure04-full200-v1/audit_portable.py --verify-frozen
```

This verifies every packet hash and every retained per-position residual record.
It does not freshly recompute the 59,813,000 channels. The native full sample
MAT arrays and source/input banks remain in retained source-bound execution
evidence and are bound individually by SHA256. No private author EPS/PDF/TeX or
original-author screenshot is distributed here.

## Fresh physical replay against the original source-bound banks

The portable path adapter imports byte-identical actual audit/math/I/O sources.
It changes only repository asset paths and adds its own before/after identity.
Supply the complete source-bound original input, native Fig. 3 result and native
Fig. 4 history banks; a fresh output folder is mandatory:

```text
python strict/validation/two-timescale-ma-native-figure04-full200-v1/audit_portable.py --inputs-bank INPUT_BANK --source-bank NATIVE_FIG3_BANK --native-bank NATIVE_FIG4_BANK --out-folder NEW_AUDIT_FOLDER --mode full200
```

The entry is deliberately bound to this actual native source/runtime/schema
identity, not an arbitrary later version, shortened bank or different backend.
It imports no production numerical kernel and runs one BLAS thread. Fixed
sample-rate1e-7, mean/design1e-9 and original stop/constraint gates are documented
in the original predeclared plan. All failures are retained. The initial v1
OneDrive progress-replacement interruption is preserved; fresh v2 reran all200
without mixing earlier results, using immutable numbered progress files.

The native history-evaluation helper is bundled as an independent implementation
asset, not author simulation code. A complete native source Fig. 3 bank must
exist before that helper can evaluate all200 Fig. 4 histories. No full Python
design-bank equivalence, historical graph recovery, complete article/all-figure
reproduction or global nonconvex optimality is claimed.
