# Isolated fixed-channel W evaluator: exact-equivalence audit

Status: **implemented in the separately frozen production v2 W block**.
The immutable original core/runner and its1-of500 completed historical bank
are retained separately. All500 v2 input jobs, configuration and manifest
are byte-identical to that bank, but all numerical jobs run afresh without
old-result reuse. This is neither a substitute W optimizer nor a claim
that all100-channel figures have completed.

## Why the original arithmetic is unchanged

During one original QT/MM W block, the RIS vector `theta`, rotations `r`,
scenario, power/noise and fixed sensing scale `iota` do not change. The original
channel builder returns `B=(F,dF/dr,bridge,G)` as a deterministic function of
`theta,r,c`, independent of W. The original utility and Euclidean gradients
can therefore be written as `E(W;B,c,iota)`. Rebuilding B at each W iteration
or building it once gives exactly the same arguments to E.

`fixed_channel_cache.py` copies **the same arithmetic/order** for E, including
the communication SINR, desired pattern, exact-iota branch, residual/NMSE,
and all W/RIS/rotation gradients. It does not change the QT/LDT variables,
sensing curvature, QCQP matrix/right hand side, dual bisection, power,
relative objective/step thresholds or original stop gates.

The fixed context stores independent theta/r copies and rejects use with a
different theta/r/scenario object. Its complete configuration snapshot is
checked after the isolated W run. Cached channel arrays are read-only.
Production rebuilds the context at **every new W block**. Reuse across
changes to theta, r or configuration is not implemented.

For a fixed initial state and deterministic original QCQP arithmetic,
equality follows inductively: same W gives same QT/MM variables and QCQP,
same W update and utility, then the same stop test. Thus every prefix and
the full final W are unchanged; this is not merely agreement of a final
objective or a looser convergence tolerance.

## Actual full-dimensional checks

The isolated audit consumed the actual completed first job of the existing
full power-b2 bank: **BS4, RIS36, users2, all66 sensing samples, all six
scheme families**. It used both each scheme's saved final state and the
original initial state. No sensing direction, hardware dimension, input
channel or W safety budget was reduced.

- Saved final-state metrics and all W/RIS/rotation gradients were bitwise
  identical to the original evaluator for all six schemes.
- An independent **scalar per-element/path-sum physical-channel oracle**
  checked final utility; maximum absolute difference was `7.99361e-13`.
- Scalar central finite differences checked W, RIS phase and rotation
  directional gradients at original full initial states; maximum relative
  error was `1.65564e-9` with declared `1e-5` test tolerance.
- Both unique initial W contexts (RIS-present and No-RIS) ran the complete
  original10000-budget block, stopping at **2828 actual iterations**.
  Uncached and cached objectives, all QCQP records, stop-gate fields and
  final complex W states were exactly equal. Their complete histories also
  matched every corresponding saved original six-scheme first W block.

The four RIS-present schemes share their initial W context before their
rotation constraints are applied; the two No-RIS schemes share another.
Those six initial runs are not six independent performance replications.
In this particular source realization some initial reflected derivatives
are physically zero. No nonzero-RIS-gradient or typical-channel runtime
claim is inferred from a zero derivative. The equivalence theorem is on
the fixed context. The later production audit additionally checked nonzero
RIS-link W/phase/rotation gradients using an independent scalar oracle.
Those are correctness checks, not a representative timing survey.

Actual one-thread W-block timings:

| Full original W block | Uncached | Fixed-channel prototype | Measured ratio |
| --- | ---: | ---: | ---: |
| RIS-present context | 51.0681 s | 1.58824 s | 32.154× |
| No-RIS context | 37.7247 s | 1.66623 s | 22.641× |

Timings are one measured run on this host with concurrent scientific jobs,
not a guaranteed whole-AO/full-bank speedup. They exclude the one-time cache
construction from the cached block timer. The saved receipt retains all
raw histories, states, hashes and scalar-oracle errors.

## Actual separately frozen v2, never mixed with old evidence

Production v2 hoists only the original deterministic channel construction
inside the unchanged W optimizer in both Python and MATLAB. Its source
fingerprint is new. The fresh named bank
`isac-power-b2-20261004-fixed-channel-v2` retains **all500 byte-identical
input jobs, configuration and manifest fingerprints**. The preserved
original version's partial outputs are historical evidence, not fabricated
theory failures and not v2 execution receipts.

The production scope is only the original W block: compute the
unchanged full channel bundle once, then reuse it for W utility calls.
Gradient/RCG/PGA cache changes, new solver tolerances, relaxed stops and
smaller channel banks are not part of this change.

The production-vs-immutable-original audit passed all six saved full-size
scheme states and all2828 initial W steps bitwise, including objective,
QCQP records, state and stop gates. It also checked all gradient families
against an independent scalar oracle on an active reflected-link scene.

The **first complete fresh v2 scenario** then ran all six original schemes
through their entire AO trajectories. Every metric, final state, full inner
history and stop measurement was bitwise identical to the actual preserved
original full-scenario result. On this host that run took87.9038 seconds,
compared with903.817 seconds for the old bank's corresponding full run:
**10.2819× measured whole-scenario speedup**. This includes channel-cache
construction and is separate from the prototype W-block timings above.
The public receipt is
[first-full-scenario-exact-version-parity.json](../validation/rotatable-isac-correctness-v2/first-full-scenario-exact-version-parity.json).

Only one complete500-bank scenario is covered by that whole-AO equality
receipt. The incomplete v2 bank has since been hash-retained and superseded
by a fresh [fixed-rotation-base v3 bank](FIXED_ROTATION_BASE_CACHE_PROOF.md),
with all500 input/configuration bytes identical and no old results reused.
No finished100-channel power point, full figure, across-channel timing guarantee
or historical-curve match is claimed. The independent MATLAB W-cache diagnostic
has also actually completed: all six scheme checks and both full2828-step
histories matched bitwise; measured W-block speedup was `31.16x` on this host.
This is a component-equivalence result, not a completed Monte Carlo figure.

```matlab
test_isac_fixed_channel_cache_matlab('new-matlab-cache-audit.json', ...
    'unchanged-full-job.json','unchanged-run-config.json');
```

The isolated reproducible audit entrypoint is:

```powershell
python strict/rotatable-isac/diagnose_fixed_channel_cache.py --scene <immutable-job.json> --config <immutable-config.json> --source-result <complete-original-result.json> --output <new-audit.json>
```

It never edits numeric files or interacts with the live bank process. It
temporarily binds the prototype only inside its own separate Python process
and restores the original function in a `finally` block.
