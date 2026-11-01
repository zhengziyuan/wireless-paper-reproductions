# Case 13: selected saved-state constraint arithmetic

This is a conditional check of **one saved statistical case**, not a new
optimization, proof of channel-model fidelity, convergence, MATLAB/Python
agreement, published-figure agreement, or complete-paper reproduction.
The historical author code and original trajectory content are not
authenticated; separately held field reads do not establish an atomic original
event or run. The implementation uses the explicitly disclosed full-J
interference and direct-NHU-link model, whose relationship to the inconsistent
printed paper equations remains a separate issue.

The earlier bounded extraction retained selected and corresponding final
states for NoRIS start 1, TwoStage start 0 and AO start 0. For all three,
saved selected W and phase values match their corresponding final W and phase
bit for bit, and the no-RIS flags agree and match the named scheme. This is
an identity check on retained values, not authentication of their producer.
The selected values and relevant saved matrices are in the lossless
`selected-input.jsonl.gz`; the uncompressed bytes are not duplicated here.

The executed calculation interprets each saved binary64 value exactly as a
rational. It independently evaluates the saved Psi matrix expression and a
separate expression constructed from the retained common NHU means and
variances. These two expressions use inputs from the same historical run;
they are not independent physical experiments. For all three schemes, all 15
full-interference NHU QoS margins are strictly positive by both calculations,
and the saved Psi matrices are exactly Hermitian. The denominator for each
calculated SINR is strictly positive. In the implementation's saved normalized
units the smallest margin per scheme is:

| Scheme | Saved Psi path | Mean/variance path |
| --- | ---: | ---: |
| NoRIS | 1.9119288977e-8 | 1.9119289009e-8 |
| TwoStage | 7.9557627608e-8 | 7.9557627640e-8 |
| AO | 7.9232131943e-8 | 7.9232131975e-8 |

The exact saved beam power is below its saved power limit for all three. The
respective margins are approximately 2.79052e-8, 2.32645e-7 and 2.31367e-7.
NoRIS ignores phase in this implementation. For TwoStage and AO, treating
the stored real and imaginary binary64 values as exact, the largest deviations
of squared phase magnitude from one are approximately 3.59891e-16 and
2.69225e-16 respectively: the **literal exact unit-modulus test fails** for
both. These extremely small representation-level discrepancies do not by
themselves show a physical failure or settle a tolerance-based feasibility
judgment. No rounded correction or changed objective is asserted here.
Positive QoS margins and a valid recorded status likewise do not establish
all propagation, numerical integration or original-paper assumptions.

The task completed naturally with the child exit observed and no guard
errors. The detached summary omits local process identity; the guard's peak
accounted output was 46,702 bytes. The monitor polls and is not a hard
filesystem quota. `recorded-assessment.jsonl` preserves the three detailed
exact results and its stream terminal; `child-summary.json` and
`guard-summary.json` preserve bounded non-identifying outcomes. The executed
worker `tools/hotspot-case13-selected-feasibility-v1/prepared_exact_assessment.py`
was bound to the execution manifest. The inputs were read from held handles;
that does not prove their historical origin.

From a complete checkout of this branch, use Python's standard library:

```text
python -I -S -B validation/hotspot-case13-selected-physical-v1/verify_recorded_assessment.py
python -I -S -B validation/hotspot-case13-selected-physical-v1/test_replay_synthetic.py
```

The replay decompresses the small retained input **in memory**, calls the
bound worker on the included stored values and the adjacent published NHU
moment projection, and checks all three exact recorded outputs. It does not
read the original trajectory or rerun the optimizer. It is a same-source
replay, not an independent implementation or proof of the model.
