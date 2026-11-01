# Two actual full Python controls on the preserved failed inputs

These are **new numerical executions** of the complete eight-scheme original
chains for cases056 and065. Their old results and failed independent float
audits remain unchanged. The new executions use the already published positive
Wick phase evaluator, with the same conditional finite-Rician model and the
same original configurations, stopping tolerances, smoothing schedule and
declared100000 phase safety cap. That cap is an unreported numerical control,
not a budget claimed to appear in the paper.

Both cases retain J3/U2/N16/M45,50 W per satellite and configured1000 moment
draws. Case056 uses kappa_L20 dB; case065 uses kappa_L0 dB. All11 original
physical input arrays match the old Python recording **byte for byte**, including
their shapes and dtypes. Power/GT limits and the complete JSON configuration
also match. Their returned1000-draw moment summaries are exactly equal to the
old returns. This does not claim a newly retained raw Python MC stream.

| New execution | Phase endpoints | Complex phase coordinates per precision | QT candidates | Largest independently checked phase norm |
|---|---:|---:|---:|---:|
| case056 |46|4140|31|9.974691633e-7|
| case065 |45|4050|35|9.968653993e-7|

All16 actual final physical states, all91 phase endpoints and all66 QT
before/after candidates pass independent MP80/MP100 checks. Every complex
phase-gradient coordinate and criterion agrees under the unchanged field
policy, every original gradient norm is strictly below1e-6, and all original
physical, QT lower-bound, tightness, primal and nondecrease checks pass.
The physical audit covers1316 scalar field values per precision, in addition
to the8190 phase-gradient coordinates. Case056's longest phase required76396
updates; it was allowed to finish under the existing cap. Actual optimization
and recording took2245.06 s and309.09 s on the local runtime.

The archive includes every original configuration, unchanged numerical JSON
return, common saved-state JSON container, actual MAT tape, execution source
binding and independent report/phase summary for both cases. The MAT files
are numerical storage from **Python execution**. Shared audit reader filenames
retain their native origin; this is not a MATLAB optimization or a new native
case. The endpoint tapes are complete for all final states/phase endpoints/QT
candidates, rather than a claim that every inner phase trajectory was saved.

This packet is distinct from the older91-endpoint positive-formula replay.
It establishes two new complete cases with new endpoint states. It does not
upgrade the old183 MP whole-case flags, establish whole-bank all183 high
precision certification, recover historical inputs, or resolve the separately
documented source-curve physical-input mismatch.

Restore every actual payload without an optimizer:

```powershell
python tools/cooperative-stable-replay/unpack_evidence.py --archive strict/validation/cooperative-corrected-python056-065-20261017/corrected-python056-065-full8-endpoint-tapes.tar.gz --expected-sha256 479d283e2873130c2b92f6aa9adfe7332b0d9fa2ab397c5d80b48389311dcaf2 --output-dir strict/outputs/corrected-python-controls
python tools/cooperative-stable-replay/audit_saved_python_case.py --result strict/outputs/corrected-python-controls/case-056/case-python-recorded.json --output-dir strict/outputs/corrected-python056-MP
python tools/cooperative-stable-replay/audit_saved_python_case.py --result strict/outputs/corrected-python-controls/case-065/case-python-recorded.json --output-dir strict/outputs/corrected-python065-MP
```

`record_python_case.py` is the actual source-bound recorder used in these two
executions. Its observer copies original returned states and records each
terminal criterion/gradient; the common JSON view is checked to retain every
original numerical return. The replayers require NumPy, SciPy and mpmath and
do not call MATLAB, a solver or a random generator.

The complete archive SHA256 is
`479d283e2873130c2b92f6aa9adfe7332b0d9fa2ab397c5d80b48389311dcaf2`.
