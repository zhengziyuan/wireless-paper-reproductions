# 17 October execution-interface checkpoint

**The complete six-paper reproduction remains unfinished.** This checkpoint
repairs execution/evidence interfaces and preserves the distinction between
parameter checks, complete scientific populations and original-reference
agreement. It does not certify all 150 figure/table tasks.

## Actual new evidence

- Python and native MATLAB each replayed both original-source parameter-table
  mappings: 36 rows, including 34 numeric rows. The independent output comparison
  matches every numeric value. The two external antenna-pattern references,
  realized physical geometry and final-publisher equivalence are not certified.
- The native result records the actual MATLAB version and retains seven
  canonical source/configuration bindings. This is a real MATLAB execution,
  rather than relabelling the Python metadata audit as MATLAB.
- The existing external CVX/SDPT3 installation was started from the migrated
  project and actually solved a dependency check. Dependencies and preferences
  are local runtime requirements; no solver binaries are distributed here.
- The targeted Python checks passed: 14 RIS/population controls, four table
  guards, 16 command-controller controls and three missing-job recovery controls.
  These are interface/host checks, not full paper experiments.

The actual outputs are [Python](actual-table-replay-python.json),
[MATLAB](actual-table-replay-matlab.json) and
[their comparison](actual-table-dual-comparison.json). Recheck the comparison:

```text
python -B compare_table_replays.py --python actual-table-replay-python.json --matlab actual-table-replay-matlab.json --output fresh-comparison.json
```

Remote CI also exposed a stale two-step hotspot RGD oracle: it seeded Armijo
with a fixed `alpha=1`, while both shipped production engines use
`alpha=1/||grad F||`. The test now independently reconstructs the declared seed
and still checks both fresh-gradient steps, ascent, the opposite-sign diagnostic
and the original `1e-13` phase comparison. Neither optimizer, stop threshold nor
paper-scene budget was changed. This is a test-control mismatch, not a newly
established paper error or a full hotspot run. The new transport/controller/
recovery tests are also included in remote CI.

## Code corrections

Both sensing RIS baseline implementations now return `target_start_banks`,
including every target's complete start summaries. Previously the renderer
correctly rejected aggregate selected-best flags, but the engines omitted the
required evidence. This is a reconstruction transport bug. Initialization,
original solver steps, quantization and the 6000/30/4000 sensing budgets are
unchanged. The native source-binding wrapper is also included as a required
central-entry dependency. Its selected aggregate flags explicitly remain
different from complete-population verification.

The two native parameter-table slots now use the actual MATLAB replay. The
controller no longer hardcodes the four old interface blocks. All 73 numerical
figures and two parameter tables remain in its two-language, 150-slot plan.
Interface availability does not imply scientific convergence or figure recovery.

Changing the returned evidence changes the source digest. Old results and
failed attempts remain associated with their original sources; they are not
silently relabelled as executions of this new source.

## Saved work and continuing scope

| Paper | Preserved evidence and unresolved work |
| --- | --- |
| MIS communications | Complete Python Fig7/Fig8 populations and the native Fig7 union are preserved. The declared array-axis/source contradictions remain explicit. Native Fig8 completion, remaining sweeps and original-reference gates require separate evidence. |
| MIS sensing | The saved Fig3 v5 Python population actually finished 6000/6000 starts: 5251 converged feasible and 749 failed/unverified, with no execution-error starts. It is not a full-convergence pass. Per-target RIS evidence is now transported in both languages. |
| Rotatable ISAC | The saved full power bank retains all 500 channel jobs, six original schemes and 100 channels per point. Its last progress file records 48 completed attempts, 12 successful and 36 failed/unconverged. Missing jobs can be resumed without overwriting those attempts; failed endpoints need separate diagnosis. |
| Two-timescale MA | The saved same-input Fig3 independent audit covers all 200 Python/MATLAB cases and reports 200 passes. Original-reference agreement remains false. Other full banks and the explicitly corrected correlated-ZF branch remain separate scopes. |
| Cooperative SatCom | The old 183-case population, failed phase/MR records and successful exact-representation repairs are retained. Parameter-table replay is now available in both languages; complete current-bank and reference-curve certification remain open. |
| Hotspot SatCom | The independently checked 18-case statistical Python population is retained, including its approximately 8.008 bit/s/Hz maximum original-reference discrepancy. Native/CDF and external-pattern gates remain open; parameter-table parity is not their substitute. |

The [all-paper issue ledger](../../ALL_PAPERS_ISSUES.md) retains precise source
errors, implementation errors and mathematical correction scopes. No failed
start is removed from a population, and no missing hardware measurement or
unavailable source is replaced with fabricated numerical data.

The [recovery command](../../../tools/resume-campaign/README.md) preserves each
full immutable MA/ISAC bank and executes only absent jobs into a fresh external
data directory. Known failed jobs remain visible. Its progress explicitly does
not certify independent physical, dual-language or reference agreement.
