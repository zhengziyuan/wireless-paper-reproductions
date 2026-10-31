# MA Fig. 20 D=3, geometry 0: native ZF AO trajectory

This is a **single-scenario, single-mode** record of an independent MATLAB
ZF theoretical AO search. The saved job uses six movable antennas, five
users, Rician factor 100, 1 W and the Fig. 20 region. Seven bounded MATLAB
segments wrote **198 coordinate updates** over **33 sweeps**, with the
configured maximum of 10,000 sweeps and the `certified_exact_2d` coordinate
subproblem. All seven guards reported natural exit. Their one-second disk
monitoring was **not a hard filesystem quota**.

The retained original native fractional-increase expression first triggered
at sweep 33. None of the recorded sweep changes was negative and every
previous sweep objective used in a stopping denominator was nonzero; the
native expression would also stop on a negative increment. This finite-run
stopping observation is neither a global-optimality proof nor an
interval-certified convergence theorem.

The bundle contains all seven native event streams, their summaries and
de-identified guard terminals, plus the saved Python Fig. 5 ZF history. It
does **not** contain the 1,000 NLoS channel samples. The Python donor records
34 sweep-boundary layouts and 198 coordinate records; intermediate positions
are reconstructed under the current source's six single-coordinate updates
in order. Current saved geometry and sample banks were separately checked for
equality, but historical producer and input identity were not reauthenticated.
The older Fig. 5 and the Fig. 20 boxes differ; the separately published
[conditional reuse audit](../ma20-zf-fig5-donor-evidence-v1/) records those
conditions and its floating polygon limitations.

The verifier checks segment/state continuity, the exact native stopping
predicate, recorded surrogate acceptance and source certificate values. It
compares all 198 native positions and objective records against the
reconstructed Python trajectory, and independently reevaluates the saved
native positions using the **current Python ZF objective**; no optimizer or
Monte Carlo samples are rerun. The maximum observed coordinate difference
was `5.329e-15`, the objective difference `1.421e-14`, and the difference
against that current formula `7.106e-15`. The minimum observed spacing was
`0.5`, and the minimum Fig. 20 box margin was `1.032413656`. These are
binary64 observations, not rigorous interval certificates or independent
authentication of the old producer.

With Python and NumPy installed, from the repository root run:

```text
python tools/ma20-native-zf-ao-evidence-v1/verify_native_evidence.py --bundle tools/ma20-native-zf-ao-evidence-v1/recorded_native_zf_events.json.gz --repo .
python -m unittest discover -s tools/ma20-native-zf-ao-evidence-v1 -p "test_*.py"
```

An initial zero-event native attempt ended with the monitor reporting
`reparse denied`; a transient profile junction was observed separately, but
the precise triggering path/timing was not retained in the guard terminal.
The failure remains in the bundle. The subsequent run precreated a normal
profile directory and kept the guard's policy of rejecting all reparse
points. The historical environment and all dependencies were not
reauthenticated, parent directories were not continuously held, and
process-level environment settings did not hard-isolate system writes.

The sample evaluation is separate from this search. This record does not
establish all per-user physical constraints, other scenarios, complete
figures, agreement with the original paper, or a full-paper pass. The bundle
is a replay record; it does not itself include the executed MATLAB helper or
the resource guard needed for a fresh optimization.
