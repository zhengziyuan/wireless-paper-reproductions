# Case 13: nearby power-constrained beam construction

For saved AO event 1327964 of start 1, the published exact binary64 audit
reported a strict total-power excess of approximately 6.31263e-9 over the
saved limit 100. This remains a genuine strict failure **of that saved point**;
the construction below does not change or erase the saved result.

Let `P` be its exact saved beam power, `P0=100`, and set `a²=P0/P`. Multiplying
every beam column by the exact positive real `a` gives total power exactly
`P0`. For each NHU, let `m=desired−τ(interference+noise)` be the previously
recorded exact QoS margin. Uniform scaling gives the exact identity

`m_scaled = a² m − (1−a²) τ noise`.

The script applies that identity to both separately saved margin sets:
moments-derived covariance and stored Psi. It matches the target event to the
next QT-begin record and start 1 final parameters, verifies that noise, power
and all 15 binary64 targets agree, and computes every margin with Python's
exact rational arithmetic. For this event, all 30 resulting margins are
strictly positive. The minimum is approximately 2.46341781147e-7 using
moments and 2.46341781115e-7 using saved Psi. The preceding original QoS audit
asserted a positive exact interference denominator for each representation;
given that assertion and positive noise, the scaled denominator is also
positive because it is `a² * old_denominator + (1−a²) * noise`.

This proves a **conditional mathematical existence statement** about a nearby
real-scaled beam, not a new optimizer output: the common square root need not
be representable in binary64, and no rounded beam was constructed. The saved
phase elements were not normalized by this calculation; unit-modulus phase
feasibility is not established. The saved records share a historical source
whose original content and atomic snapshot were not authenticated. The result
does not prove the physical propagation model, convergence, MATLAB behavior,
agreement with the paper or complete reproduction.

From the repository root, using Python's standard library:

```text
python -I -S -B tools/hotspot-case13-power-rescaling-v1/check_saved_power_rescaling.py
```

The input files are the previously published exact QoS record, QT-parameter
record and final-parameter projection in adjacent tool directories. The
script reads them only and prints a small JSON result. For review against the
independently retained original rational QoS computation, run the saved QoS
reader documented in `../hotspot-case13-evidence-v1/README.md` separately;
this construction does not recalculate those input margins.
