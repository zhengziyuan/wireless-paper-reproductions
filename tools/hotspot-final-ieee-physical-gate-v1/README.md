# Conditional saved-phase gate for the final-IEEE candidate

The current Python statistical runner's `physical_constraint_pass` uses its
saved total-power and NHU-SINR evaluation, but it does not inspect the RIS
phase vector. The corresponding new MATLAB candidate likewise reports that
flag from power and SINR only. Therefore that original flag alone cannot
certify the phase unit-modulus constraint. No actual bad phase is implied by
this structural observation.

This independent **post-hoc** reader leaves the original algorithms, stopping
rules, records, budgets and reported flag unchanged. For TwoStage and AO it
inspects the 25 saved final-phase components; for NoRIS the phase is not an
applicable constraint but the saved `no_ris` flag must match its scheme. It
requires an explicit caller-supplied nonnegative finite tolerance for
`max(abs(real(phi)^2+imag(phi)^2-1))`. It separately reports whether the exact
binary64 values have zero error and whether their exact rational error is at
most that tolerance. No scientific tolerance is invented or authenticated by
this code. Different tolerances may change the conditional result.

Invalid shape or observed nonfinite elements fail the phase check. Missing
phase, scheme identity, execution flag, no-RIS flag or original physical flag
cannot produce a pass. The case function requires every distinct start ID
`0..U` in each of the three schemes and checks case identity. A known failure
dominates an unknown when aggregating. Duplicate IDs and absent records are
unknown; no matching record is invented. Only unique identifiable starts are
assessed. `True` is **conditional** on the original reported power/SINR flag,
the supplied tolerance and source data. It is not an independent audit of
power, QoS, propagation, solver convergence, or the original paper; the output
always retains explicit false fields for an independently verified full
physical or paper pass.

No MATLAB runtime or real scientific scenario was executed for this tool.
It has not been integrated into either production runner or used to recertify
historical records. An eventual production integration must bind its input
states and declared tolerance to independently reviewed source/configuration
and preserve all original outcomes. The existing known case-13 saved states
had phase squared-magnitude errors near 1e-16; this observation alone is not a
physical failure and is not used as a default tolerance.

Run the synthetic standard-library checks from the repository root:

```text
python -I -B -m unittest discover -s tools/hotspot-final-ieee-physical-gate-v1 -p test_recorded_physical_gate.py
```
