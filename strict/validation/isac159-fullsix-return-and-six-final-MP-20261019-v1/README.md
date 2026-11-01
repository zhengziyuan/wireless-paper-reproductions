# Original case159: full six-method return with two retained inner failures

This is the actual cold full-budget return for original case159, using the explicit self-excluded interference and structured positive-alpha Q/P arithmetic variant. The eight implementation source files are byte-identical to those used for the saved run. The original scenario and all 28 configuration members are unchanged. The cold initializers, six methods, PR/BB behavior, acceptance tests, and AO500/W10000/RCG500/PGA500 budgets remain in the frozen implementation.

The original run returned **2** after 833.713 seconds: all six methods executed, met their original outer stop, and satisfied recorded power and rotation constraints. Four methods met the complete original stopping checks. **Rot-BS & Rot-RIS and Rot-BS & Fix-RIS did not:** their final RIS phase blocks exhausted 500 updates above the original normalized-gradient tolerance of 1e-6. This is an incomplete convergence result, not a completed paper reproduction. There was no scientific exception; the passive exception record is empty rather than fabricated.

Independent MP80 and MP100 evaluation of all six saved final states passed the physical fields, feasibility and fixed-iota derivative comparisons. Maximum W/RIS/rotation component errors were 1.04662e-15 / 8.12390e-15 / 1.89419e-14. The largest MP80/MP100 derivative or objective difference was 4.88375e-60. These comparisons use disclosed reader tolerances; they do not replace original algorithm stops.

For Rot-BS & Rot-RIS, the last rotation block made zero updates, so the actual final state is also the historical last phase endpoint. Its MP gradient norm is 1.50961922669e-5, confirming the original failed stop; its difference from the saved norm is 1.62190e-17. Rot-BS & Fix-RIS made three subsequent rotation updates. Its current final-state phase norm is 9.89379418996e-6; this is explicitly not a reconstruction of its earlier pre-rotation phase input.

The complete returned trajectory and the full six-state MP report are retained as gzip JSON in `evidence/`. Only absolute local provenance paths were projected to `retained-evidence/` identifiers. Numerical values, failure flags and history arrays were preserved. Such identifiers are provenance labels, not download locations. The included source manifest uses relative input paths but preserves all eight source and both input digests; the historical manifest digest in the old return remains its original identity. See `provenance.json` for original and public artifact identities.

## Read or re-evaluate the saved states

Use Python with NumPy. The following bounded command only loads the six saved states and the frozen numerical provider. It performs no optimization, random sampling or new MP evaluation:

```console
python -B check_saved_final_provider.py --output <new-check-result.json>
```

The packaged saved-provider command was actually executed once. All six saved-state physical fields matched the frozen provider exactly, and its source identities remained unchanged; see `evidence/portable-saved-provider-first-use.json`. This is a saved-provider check, not an additional independent physics or convergence result.

The exact independent six-state MP adapter is also included, with a relative-path replay plan. From this package directory inside the repository checkout, Python with NumPy and mpmath can replay the bounded saved-state audit:

```console
python -B audit_actual_six_saved_final_states_and_exact_phase_boundary_MP_v1.py --plan saved-six-MP-replay-plan.json --output-dir <new-MP-output-directory> --execute
```

The adapter source is byte-identical to the completed MP execution. Its public plan changes only file bindings and corresponding projected-artifact identities. That relocated MP command has been statically checked, not re-executed during packaging.

The already-completed independent MP result is evidence for fixed saved states only. Historical QCQP/KKT correctness at every intermediate iterate, a new complete native MATLAB trajectory, original-reference agreement and whole-paper completion remain unproved here. The source scenario records which quantities were reported and which were reconstructed; a reconstructed budget is not newly attributed to an unreported author experiment.

## Execute the original full-budget six methods

Choose a new output directory that does not already exist. This is a real optimization run; the saved execution above is already complete and need not be repeated to inspect it.

```console
python -B run_case159_equivalent_fullsix_v1.py --config original-config.json --scenario original-scenario.json --output <new-output-directory>/full-result.json
```

Exit0 requires all six original checks, exit2 retains incomplete original convergence, and exit1 records a host/source/uncaught failure. The positive-alpha structured solver has domain guards without jitter, eigenvalue clipping, rank truncation or a fallback solver. The original assembled Q/P residual remains an explicitly labeled diagnostic; it is not the input to the structured solve and no new stationarity cutoff is imposed. The earlier fixed-QCQP dual-language evidence is in the sibling `isac159-structured-original-qcqp-fixed-state-20261019-v1` package.
