# Case 13: analysis of recorded stopping histories

This is a **saved-record analysis**, not a new optimization, proof of
mathematical convergence, original-paper agreement, or full reproduction. It
uses the previously extracted fields for one statistical case (U=1,
satellite Rician factor 20 dB) from `../hotspot-case13-saved-stop-history-v1/`.
The original historical source content has not been authenticated; held file
identities are not a historical-content certificate, and separate reads do
not establish an atomic original event or run.

The consumer examined 28 expected events: four QT-loop ends, ten phase ends,
eight AO-iteration records, and six final-execution records. No negative
adjacent objective difference was reported in the examined saved sequences.
An independent saved-sequence count covering four QT histories, ten phase
histories, and the two final AO histories has 105 comparable adjacent pairs,
all nonnegative; one of the phase histories has only one point. Histories in
other records overlap or repeat these sequences, and the event counts are not
counts of independent optimizations. Two TwoStage final records have separate
QT and phase histories; no difference between those two blocks is formed.

The four QT-loop and ten phase-end stop records report `converged=true`; their
reported iteration counts match the corresponding saved history lengths,
and the checked residual or gradient-norm comparisons show no mismatch at the
consumer's stated mixed numerical threshold. Six final-execution records
report algorithm success. Those are **recorded flags**, not an independent
validation of all stopping conditions or solver/physical feasibility. In
particular, these observations do not prove that unrecorded steps did not
decrease, that all QT inner solves or convergence histories are present, or
that the optimizer's exact Armijo increments equal rounded history differences.
The new independent audit gate has not been inserted into production.

`recorded-analysis.json` is the retained consumer output. The consumer reports
each saved event, any negative recorded steps, missing/unsupported nested
fields, saved flags, and discrepancies it can check. Its event/history coverage
flag does not certify all 74 extracted fields or a complete original
trajectory. `verify_report.py` reads the lossless compressed event stream
directly with bounded decompression, reruns the consumer, and compares the
result with the retained report. It does not read original trajectory chunks,
rerun the optimizer or recalculate channel physics. Because the report
contains binary64 calculations including a library gradient norm, exact
report equality is a same-arithmetic replay check; a mismatch on another
runtime requires review rather than automatic scientific-failure inference.
The original command that produced the retained analysis did not pin the
consumer source bytes before execution. Replaying the current consumer source
and obtaining the same report does not authenticate the bytes executed by that
earlier command; it is a present-day arithmetic reproduction of the report.

From a complete checkout of the branch, run with Python 3:

```text
python -I -S -B validation/hotspot-case13-saved-stop-analysis-v1/verify_report.py
```

The replay reads only the adjacent recorded report, the retained compressed
event stream and child summary, and the published consumer source. It writes
its compact result to stdout; it does not create a decompressed copy.
