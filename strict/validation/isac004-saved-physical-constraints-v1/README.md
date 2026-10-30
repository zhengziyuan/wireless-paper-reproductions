# Saved-state physical checks for an interrupted ISAC004 No-RIS run

This is a diagnostic of **one saved intermediate state**, not a new run and not a
successful reproduction. The original Rot-BS & No-RIS run failed because its
exact sensing-scale update encountered zero overlap with the desired pattern.
The [related original failure and paper Eq. (19) evidence](../isac004-paper19-saved-state-v1/README.md)
records that condition in more detail. Its original state must not be treated as
a converged result.

The input is a small lossless selection of saved numerical arrays and relevant
configuration values from this failure state. The arrays retain their saved
binary64 values. It contains no private local paths or full source trees. The
fixed-RIS phase is merely a placeholder for a zero-bridge No-RIS baseline.

The checker computes beamformer power, tests the configured rotation bounds and
independently sums the per-beam interference plus noise before computing rates.
It compares those quantities with the saved rate and interference. Power is
reported both exactly as evaluated in binary64 and with the source-configured
verification tolerance; do not silently round its slight boundary excess away.
Low individual rate is a description of this one state, not evidence of a QoS
or fairness violation. These checks do not prove physical correctness of the
channel geometry, end-to-end feasibility, MATLAB/Python agreement, convergence
or agreement with published figures.

Run with Python 3 and NumPy, selecting a **new** output file; existing files
are never overwritten:

```text
python replay.py --input-dir . --output /path/to/new-output.json
```
