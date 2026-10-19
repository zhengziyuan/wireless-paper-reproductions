# Native supplement: MA Figure 19, D=3, geometry 1

This supplements the [published Python case](../ma-figure19-statistical-D3-g1-20261019-v1/README.md). It preserves actual independent MATLAB statistical searches and each winner's evaluation on the same original **1000 fixed saved NLoS samples**. The user selected this lower-computation statistical design target; the author's historical search criterion remains unknown.

Both native searches and both native final evaluations returned naturally with code 0. Each actual original process handle verified initial/terminal PID, birth and exit, and each watched source/input interval closed unchanged. The initial client WMI type error and first native pre-model path-admission failure (code 1, before model/search execution) remain in the evidence. Only command/admission path spelling and fresh output directories changed; scientific sources did not change.

## Actual numerical return

The scene is N=4, M=3, kappa=100, P=1 W, D=3 on [-1.6,1.6]^2. Both native modes selected MATLAB indices [1,4,6,9], corresponding to Python [0,3,5,8]. The actual positions are [-1.6,-1.6], [0,-1.6], [0,1.6], [1.6,1.6].

| Mode | Native nodes / leaves / prunes | Native statistical value | Native original1000 mean sum rate |
|---|---:|---:|---:|
| MRT | 67 / 31 / 16 | 13.950221964703815 | 14.351012257599148 |
| ZF | 73 / 37 / 14 | 14.60241474915847 | 20.44070513545616 |

These are complete branch-and-bound searches of the selected native frozen statistical models, not reduced grids. Native comparisons use exact rational products of Eq.13/Eq.39 factors; logarithms are display values only. The implementation uses BigInteger rational arithmetic, exact complex Gauss-Jordan elimination and conservative directional/Schur/trace/Gershgorin bounds.

Python ZF used 70 nodes, 34 leaves and 15 prunes; native ZF used 73/37/14. Each language freezes its own binary64 primitives. Their exact rational products are **not equal**: relative differences are 4.681266151286414e-15 (MRT) and 2.915907684885353e-16 (ZF). Actual winner position bits match here. No complete search-trajectory identity, exact cross-language theoretical-model identity or general winner equivalence is claimed. No data were adjusted to force agreement.

## Existing actual independent check

One saved-only check reused the published independent binary64 channel/MRT/ZF-QR functions. It read both native winners on all1000 original samples and compared actual Python returns. It returned 0 with its selected source/input interval unchanged. Maximum native physical-reference sample-rate errors were 3.552713678800501e-14 (MRT) and 7.105427357601002e-15 (ZF); mean errors were 5.329070518200751e-15 and 3.552713678800501e-15. Fixed-point statistical-value errors were 5.329070518200751e-14 and 1.2079226507921703e-13. Existing tolerances remain 1e-7 for samples and 1e-9 for means, powers and fixed-point values. No tolerance changed.

This is independent binary64 physics, not a full multiprecision or interval proof. It does not replay every global-search pruning certificate. Native search retains a frontier, rolling digest and last witness rather than an independently stored witness for every discarded subtree.

## Portable saved-data reader

Requires Python 3.10+, NumPy and the sibling Python capsule linked above. The shared fixture SHA256 is `09b8c681ad40ffb0021c49746f656ba1fca65cc080845e06a67e0912c6374182`; `sources/independent_saved_physics.py` has SHA256 `9db2b29a4d2235122feb3438c2a47ffe8fdebfce738b6bf3779c4d0a7cc2b81d`. The original job/config UTF-8 in that fixture bind all1000 inputs, so they are not duplicated here.

```console
python -X utf8 -B read_native_saved_supplement_v2.py --output-dir <fresh-output> --execute
```

Use `--python-capsule <directory>` when the dependency is elsewhere. The reader consumes JSON/gzip and base64 numeric bytes only. It does not load pickle or MAT, invoke MATLAB, perform search/optimization, or call RNG. It verifies public bytes, reconstructs the published native primitive numeric bytes/shapes, and repeats fixed-state physics/dual comparison. The packaged adapter was then executed **exactly once** outside the capsule and returned naturally with code 0. Its original process handle verified birth/exit and the complete finite source/input epoch remained unchanged. Both native1000 physics and saved dual comparisons passed. `portable-first-use.json` preserves the actual result and lifecycle evidence. The earlier fixture preparation flag is historical and is superseded by this actual first-use record.

The fixture includes complete search summaries, all1000 rates/powers/off-diagonal amplitudes per mode, native frozen primitive real/imaginary IEEE bytes and shapes, process closure facts, original source digests and actual independent comparisons. Primitive transport directly from saved native MAT passed numeric byte/shape round trips. The original MATLAB typed digest is retained as producer provenance; this reader does **not** reproduce that separate hashing protocol. Public gzip and field-payload digests independently identify public bytes.

## Sources and limits

All eight actual native exact-search source files appear unchanged under `sources/native/`. The final-evaluation entry is the ninth file; identical native bridge/IO dependencies are shared. The bridge includes complete original `ma_scenario`, `ma_los`, `ma_covariance` and `ma_instantaneous` local functions. Recorded paths need no external repository core, CVX, Symbolic Toolbox, AO/FPA solver or channel sampler. Fresh execution requires explicit new admissions with current local input/source paths and actual original-handle lifecycle records; the sources do not authorize an automatic campaign.

Full original MAT evidence remains local with original digests listed; no original MAT or large stream is claimed uploaded. No private PDF, author archive or private absolute path is included. This is one D3/g1 result: full 1600+1000 Figure19/20 completion, earliest exact tie/global certificate replay, all-axis dual equivalence, historical author criterion, original reference curves and the six-paper goal remain unclosed by this capsule.

The portable first use retained a MRT fixed-point error of 4.618527782440651e-14, while the prior private MAT-based reader retained 5.329070518200751e-14. Both are below the unchanged 1e-9 design tolerance. Both actual results remain recorded; complete floating-point output identity between the two reader invocations is not claimed. Scientific runtime, fixture and reader bytes were unchanged during first use; only this evidence, README and manifest were updated afterward.
