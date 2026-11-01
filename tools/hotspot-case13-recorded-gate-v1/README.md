# Case 13: conservative gate on associated saved records

This is a read-only interpretation of already-published, **single-case saved
records**, not a new optimization, proof of convergence, physical validation,
or paper reproduction. It combines only the bounded stop-history projection
and the bounded final-result projection previously published under
`validation/hotspot-case13-saved-stop-history-v1/` and
`validation/hotspot-case13-final-mc-v1/`. No historical trajectory chunk is
reopened and no channel or optimizer is run.

The final AO output does not itself contain inner phase histories. However,
the retained event stream separately contains eight `phase_end` histories,
four for each AO start. This reader associates them with the two final AO
records using scheme, start and ordinal; the complete retained typed stop
structure must match the corresponding final block, including extra controls
and backtrack counts. Numeric binary64 values are compared bitwise, including
signed zero; nonfinite numbers are rejected. Dictionary key order is immaterial,
but the stored ordered field-name lists must match. The immediately following
AO event must have the same complete typed phase-stop structure,
and its saved outer history must match the corresponding final-history prefix
bit for bit. The two NoRIS QT histories and the two TwoStage phase/QT histories
are also checked against their corresponding final records and stop fields.
One of the eight AO phase histories contains only one saved point.

`recorded-gate.json` is the output of the existing independent
`hotspot-final-ieee-convergence-gate-v1/recorded_gate.py` after these explicit
associations. **All six starts and the case remain `null` (unknown)**: the
historical producer and completeness of capture are not authenticated, and
the actual historical limits are not independently bound. The compact final
projection also does not contain the case-level `status` field expected by
the gate; this reader deliberately does not invent that field. These `null`
results are evidence gaps, not successful stops, false failures, or proof that
the author's original configuration had a particular budget.

The gate was designed for the current Python record schema; the associated
events are separately serialized historical records. Converting exactly
integral stored stop counts to integers adapts their representation only.
The tool does not authenticate the original code or establish that separate
field reads form an atomic event. Matching stop fields and outer prefixes makes
the association explicit; it cannot prove there were no omitted events or that
all inner histories were captured. The saved parameter set also differs from
the final IEEE Fig. 10 nominal defaults; see
`../hotspot-case13-final-default-mismatch-v1/README.md`.

From a complete repository checkout, run the standard-library verifier and
synthetic association tests:

```text
python -I -S -B tools/hotspot-case13-recorded-gate-v1/check_recorded_gate.py
python -I -S -B tools/hotspot-case13-recorded-gate-v1/test_synthetic.py
```

The verifier prints a report; compare it to the retained `recorded-gate.json`.
The synthetic tests reject event/stop/prefix mismatch and verify that a known
negative step remains false even when other evidence is unknown. They do not
prove the historical data or mathematical convergence.
