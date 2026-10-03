# Exact fixed-rotation channel-base reuse

This changes deterministic evaluation cost, not the channel model, original
QT/MM/RCG/PGA algorithms, tolerances, iteration budgets or input population.
It follows the earlier [fixed-W channel proof](FIXED_CHANNEL_CACHE_PROOF.md).

## Algebra and arithmetic order

Within one original RIS RCG call, `W`, rotations `r` and the channel realization
are constant; only `theta` changes. The direct channel `h`, RIS–user channel `g`,
BS–RIS bridge `B` and their rotation derivatives therefore do not depend on
`theta`. Compute these six base arrays once from the unchanged original path
loops. Every evaluation still constructs

`f_m = h_m + B @ (theta * g_m)`

and the original rotation Jacobians in the original order. The phase derivative,
all three gradient families, sensing responses, utilities and line-search values
are evaluated using those unchanged expressions. This does not cache a gradient
or objective across different `theta`, approximate a channel or reorder a sum.
Each RCG call owns its base; after an outer rotation update a new base is built.
No-RIS uses the original zero bridge. Python/MATLAB also retain an uncached
diagnostic route for direct equivalence checks.

## Actually executed Python production checks

The separately saved source-bound v3 audit compared against the complete,
hash-retained v2 implementation and against the current uncached diagnostic path.
It used the original dimensions, all six schemes, saved and perturbed phases,
and an exported active-RIS full-channel case. All channel fields/Jacobians and
all three gradient families were bitwise equal; independent scalar checks were
also retained. Both distinct full2828-step W blocks matched complete states,
objective/QCQP histories and stop gates. The active-RIS full500-step RCG call
matched every state, raw PR, transport/retraction, Armijo/restart and stop record.
Its `capped_unconverged=true` was retained, not converted to convergence.

A fresh complete six-scheme first scenario took `85.854337 s` and matched all
metrics, states, inner histories and stopping records bitwise against the
retained v2 result. The measured active-RIS block speedup was `22.5632x`; this
is one measured block, not a claimed speedup for every scene or a full sweep.

These are actual Python checks. The MATLAB test is provided separately and its
success must be determined from its actual receipt, not this proof:

```matlab
test_isac_fixed_rotation_cache_matlab('new-matlab-v3.json', ...
    'jobs/case-000-mc-000.json','run_config.json', ...
    'jobs/case-000-mc-001.json');
```

## Frozen full-bank transition

All available v2 sources/configuration, all500 input files, actual pass/fail
receipts and in-flight observations were byte-verified and retained before the
authorized version transition. Only the verified owned v2 executor/children
were stopped. Its unfinished scenarios were not relabelled numerical failures.
The v3 scientific identity is distinct. Its fresh500-job bank contains exactly
the same input/configuration/manifest bytes and starts without any old numerical
results. Each channel still runs all six original schemes and original stop
gates; nothing is averaged until the complete required bank passes.

The actual first fresh v3 bank job passed; the full500-job bank remains in
progress. There is no complete-figure or original historical-curve agreement
claim from this acceleration proof.
