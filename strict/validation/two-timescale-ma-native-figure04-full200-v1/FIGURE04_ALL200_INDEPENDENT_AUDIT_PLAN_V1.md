# Predeclared independent native Fig. 4 history audit

This WORK-only evaluator is outside every running/frozen scientific package.
It does not optimize positions, import a production numerical kernel, change
the finite sample bank, or select successful geometries. Native Fig. 4 reuses
the complete original Fig. 3 ZF design trajectories and evaluates the same
1,000 saved NLoS draws at every recorded position. The first position is the
initial geometry: the expected 59,813 positions include 200 initial states and
59,613 post-sweep states, not 59,813 new accepted updates.

Required inputs are all 200 jobs of `ma-figure03-20261004-ao10000-v2`, all 200
actual native source results in its `-matlab-source-v2` bank, and all 200 native
history JSON/MAT pairs in `ma-figure04-native-derived200-20261004-v1`.
Before any numerical work, freeze all their hashes, configuration, plan,
manifest, both native execution receipts, native derivation helper, this plan,
the audit entry, and the independent public physical evaluator. Check actual
source/input fingerprints and the native before/after bindings. After the
audit, recompute every frozen file hash. Never overwrite earlier evidence.

For every recorded N=6, M=5 position, rebuild the original iid-Rician channel
from its original geometry and all 1,000 complex NLoS arrays. Compute the
minimum-norm ZF beam via QR and a triangular solve, rather than the native
normal-equation inverse. Check every saved sample sum rate, every saved mean,
each sample's transmit power and relative ZF off-diagonal residual, and the
saved maximum power/leakage arrays. Independently reconstruct the original
Eq. 39 statistical design objective, all spacing/box constraints, the initial
state, and the final fractional-increase stopping condition. Source flag
values alone cannot establish these gates. The first and final position of
the first full case additionally compare all 1,000 batched QR beams/rates
against independent scalar SVD minimum-norm solves.

Predeclared comparisons inherit the prior complete native physical audit:
sample-rate absolute tolerance 1e-7, saved mean and statistical objective
absolute tolerance 1e-9; the original spacing/box verification tolerance and
5e-5 stop are read from the unchanged configuration. Power equality uses the
native evaluation tolerance 1e-10 times max(1, P); saved power-error replay
uses 1e-12 times max(1, P). Relative off-diagonal amplitude is divided by the
maximum diagonal H^H W amplitude of that sample and must be <=1e-9. The saved
absolute leakage replay is a secondary arithmetic comparison (absolute
1e-15); it is not used instead of the scale-normalized physical ZF check.
QR/SVD scalar rate comparison uses the same 1e-7 sample-rate tolerance.

Each case saves residuals/checks for **every** position; exceptions and failed
gates are retained. A full pass requires all 200 cases, all 59,813 positions,
all 59,813,000 saved sample rates, unchanged hashes, and the fixed comparisons.
`--prepare-only` performs only binding/hash inventory; it is not a numerical
audit. `--mode preflight-first-case` is explicitly one case, not 200. Heavy
full execution is not started by preparing this entry and requires the
parent's resource coordination. One process, one BLAS thread maximum.

This is a dual-implementation physical-evaluator cross-check of a trajectory
reuse protocol, not a new position optimization, native/Python full design
bank equivalence, agreement with the historical plotted Fig. 4, a global
nonconvex optimum, or completion of the article's remaining figures.
