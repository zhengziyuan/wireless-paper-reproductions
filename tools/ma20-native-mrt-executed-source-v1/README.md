# MA Fig. 20 MRT: executed native components and portable driver

This package makes the native source behind the separately recorded
[eight-segment trajectory](../ma20-native-mrt-ao-evidence-v1/) reviewable.
It concerns one theoretical MRT AO scenario; it is **not** a full figure or
paper implementation or acceptance claim.

- `ma_original_statistical_components_native_v1.m` and
  `generate_component_dispatch_prepared_v1.py` are byte-for-byte copies of the
  helper and generator bound by the first native execution manifest. The
  generator exposes the helper's existing `coordinate` and `mrt_value`
  functions without changing their numerical bodies.
- The exact 2D solver used by this experiment is the repository's
  [`ma_exact_coordinate.m`](../../strict/two-timescale-ma/ma_exact_coordinate.m),
  whose bytes match the bound native runtime solver.
- `ma20_mrt_segment_prepared_v1.m` is a **portable adaptation**, not the
  exact executed driver bytes. Its only changed line replaces an output-path
  assertion containing a machine-specific absolute path with an assertion
  against `MA20_NATIVE_OUTPUT_ROOT`. All other original driver lines,
  including coordinate and stopping calculations, are byte-for-byte equal.
  `source_bindings.json` records both hashes; the de-identified
  `execution_first_manifest.json` retains the actual first execution's source
  pins. These records do not independently authenticate historical producers.

Check the published hashes and six numerical component bodies against the
repository's `full_v4` MATLAB source with:

```text
python tools/ma20-native-mrt-executed-source-v1/verify_source_bindings.py --repo .
```

If the original execution driver is independently available, append
`--original-driver` followed by its path to verify its manifest-bound hash and
the exact one-line difference. The standard check intentionally reports that
this optional original-driver comparison was not performed when it is absent.

The executed helper and its segmented driver use the original literal
fractional-increase test. `run_strict_two_timescale_ma_full_v4.m` uses
`ma_fractional_stop_v3`, which treats a negative increment and zero previous
objective differently. Those semantics must not be silently interchanged. In
the eight recorded segments all 39 sweep increments were nonnegative and the
previous sweep objectives were nonzero, so this distinction did not change
the recorded stopping decision.

For a separately authorized experiment, run the included generator with the
bound helper, its `source_bindings.json` hash and an output filename exactly
`ma20_original_components_exposed_prepared_v1.m`; add that generated file,
the portable driver, and the repository solver to the MATLAB path. Set
`MA20_NATIVE_OUTPUT_ROOT` to the chosen output directory and supply the job,
configuration, fresh event path, and either `[]` for the first call or a
validated prior state to the driver. The 1000-sample input bank is **not**
included here, even though the theoretical AO update does not consume those
samples. Source checks alone do not authenticate its historical identity.

The portable path assertion is only a convenience check, not a filesystem
sandbox or a security boundary. These files do not provide the original
external process/storage guard or a production successor lease. Independent
input binding, one-writer control, bounded storage and recovery procedures are
still required before a new run. No original saved trajectory or failed guard
receipt was modified to prepare this source package.
