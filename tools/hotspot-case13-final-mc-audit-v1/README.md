# Case 13: arithmetic audit of saved MC summaries

This utility checks an already extracted case-13 saved-result projection; it
does not read historical trajectory chunks or generate fading channels. For
each of the exact scheme keys `NoRIS`, `TwoStage`, and `AO`, it separately
consumes that scheme's `independent_MC.hu_rate_samples`, checks its length
against the saved count, and independently recomputes the sample mean and
sample standard error. The computation uses `math.fsum`, sample variance with
denominator `n-1`, and division by `sqrt(n)`. It reports the differences from
the recorded figures; the differences are not replaced by rounded values.

The saved example contains 1000 values for each of the three schemes. The
largest absolute difference from a recorded mean is about `1.78e-15`, and the
largest difference from a recorded standard error is about `4.34e-19`.
These are arithmetic checks on saved vectors, not proof that the underlying
1000 channels were statistically independent, genuinely drawn, or match
the original authors' simulation. The comparison also does not independently
reconstruct the ratio-of-empirical-powers rate.

The tool preserves the reported start identifiers, their individual check and
status flags, prescribed/executed/selected identifiers and ensemble flags.
It explicitly reports missing starts, recorded failures, and disagreements
between start and ensemble reports; it does not treat flags as independent
feasibility or convergence checks. The selected ID belonging to a saved start
is not proof that the selection rule was implemented correctly, since the
saved projection does not contain all candidate selection scores.

Input is the bounded single-record
`CASE13_FINAL_RESULT_BOUNDED_PROJECTION_V1`. Its retained two-field extraction
used the existing case-13 index and per-chunk identity lock; this does not
authenticate historical source bytes or establish an atomic whole event.
The saved geometry, original figure reference agreement, MATLAB/Python
equivalence and physical feasibility remain unverified. There is no paper
or science PASS in this tool or its output.

The first execution of this arithmetic audit did not pre-bind its source
bytes; a later replay that obtains the same report establishes present-day
arithmetic repeatability, not the exact source identity of that first run.

From the repository root, after obtaining the retained input projection:

```text
python -I -S -B tools/hotspot-case13-final-mc-audit-v1/audit_recorded_mc.py <projection.jsonl>
python -I -S -B tools/hotspot-case13-final-mc-audit-v1/test_audit_recorded_mc.py
```

The synthetic regression includes a mismatched sample count, missing and
failed starts, incorrect selected ID, nonfinite samples and invalid flags. It
does not run the original optimization or perform a scientific experiment.
