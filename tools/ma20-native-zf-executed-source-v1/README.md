# MA Fig. 20 ZF: executed native components and portable driver

This package documents the MATLAB source used for one theoretical ZF AO
scenario. It is a conditional reproduction component, not an acceptance claim
for the full figure or paper.

- The numerical helper is the previously published
  [`ma_original_statistical_components_native_v1.m`](../ma20-native-mrt-executed-source-v1/ma_original_statistical_components_native_v1.m).
  The helper's bytes match the ZF first-execution manifest. It is referenced
  instead of copied. The ZF generator here is the exact first-execution source
  and exposes the helper's existing `coordinate` and `zf_value` functions
  without changing numerical bodies.
- The exact 2D solver is the repository's
  [`ma_exact_coordinate.m`](../../strict/two-timescale-ma/ma_exact_coordinate.m),
  whose bytes match the bound native runtime solver.
- `ma20_zf_segment_prepared_v1.m` is a **portable adaptation**, not the exact
  executed driver bytes. Only its sixth line changes: the original check of a
  machine-specific absolute output root becomes a check against
  `MA20_NATIVE_OUTPUT_ROOT`. Every other line, including the numerical and
  stopping logic, is byte-for-byte equal. `source_bindings.json` records both
  hashes; `execution_first_manifest.json` is the first execution's path-free
  manifest. These pins do not authenticate historical authors or producers.

Check the published source and six numerical component bodies with:

```text
python tools/ma20-native-zf-executed-source-v1/verify_source_bindings.py --repo .
```

If the original local execution driver is independently available, append
`--original-driver` and its path to additionally check its recorded hash and
the exact one-line difference. The default command reports that this optional
original-driver comparison was not performed.

The executed helper and driver use the literal fractional-increase stopping
expression. The repository's `run_strict_two_timescale_ma_full_v4.m` uses
`ma_fractional_stop_v3`, whose negative-increment and zero-previous-objective
handling differs; those branches must not be silently treated as equivalent.
The separately recorded [ZF trajectory](../ma20-native-zf-ao-evidence-v1/)
contains 33 completed sweeps, all with nonnegative increments and nonzero
previous objectives; for those observed sweeps this distinction did not change
the stopping decision. Source checks alone do not establish convergence,
global optimality or original-paper agreement.

For a separately authorized experiment, run the included generator with the
linked helper, its bound hash in `source_bindings.json`, and an output filename
exactly `ma20_zf_components_exposed_prepared_v1.m`; add the generated file,
the portable driver and repository solver to the MATLAB path. Set
`MA20_NATIVE_OUTPUT_ROOT` and supply the job, configuration, fresh event path,
and either `[]` or a validated prior state. The 1,000-sample input bank is
not included here and its historical identity is not authenticated.

The portable output-root check is not a filesystem sandbox. This package does
not include the original external resource guard or a production successor
lease. Independent input binding, single-writer control, bounded storage and
recovery are required before a new run. No original execution file, trajectory
or failure record was modified in preparing this package.
