# Complete183 selected Python phase recordings

Every original slot0..182 retains every actual saved phase context, endpoint,
criterion and complete complex gradient reference. Independent MP80 and MP100
checks pass for all8362 phase endpoints and417910 complex gradient coordinates
per precision. The original strict gradient-norm stop remains `<1e-6`; field
comparison remains `1e-9+1e-10*abs(reference)` and the precision bound `1e-40`.
Each full original scene configuration and J/U/N/M dimension is bound to the
original183-case source index. No optimizer or production RNG is called.

An additional independent MP80/MP100 calculation checks every actual phase
coordinate against the unit-modulus domain, using the original1e-10 bound.
All8362 endpoints pass; the maximum actual unit-modulus error at MP100 is
0.000000000000000332874942396774953481019259014929700502028825056113523993138078548772959169885739895080133076413342294849.
The complete per-endpoint domain report is retained in numbered gzip parts;
its separate manifest gives both the compressed and decompressed hashes.

The full input/reference archive is391937442 bytes, SHA256
`055c7ade93f8d2457d21b5cdb90b11c5a1911169519e4c214109b7f92c69f84b`.
All748 parts and915 numerical/reference payloads are required. Every one of
the8362 original phase JSON reports and every case summary remains byte-for-byte
inside per-case stored ZIP members. The full MAT contexts and actual lossless
adapter/roundtrip receipts are included. The archive also retains the complete
183-case journal and actual phase-controller terminal0/source-closure receipt.
The historical056/065 failed epochs remain separate from their selected new
same-input epochs; this packet does not overwrite or relabel the failures.

Install NumPy2.5.3, SciPy1.18.1 and mpmath1.4.1, then use a fresh destination:

```text
python -B tools/cooperative-stable-replay/replay_complete_python_phase183.py --packet strict/validation/cooperative-Python183-complete-phase-20261017 --output-dir new-Python183-phase-replay
```

Default replay and the separate CI job freshly evaluate all183 gradient and
criterion tapes at both precisions, compare every complete reference, and
freshly check all8362 phase domains. The240-minute CI allowance is an
infrastructure limit and changes no scientific budget or stopping condition.
The actual CI result for a new commit must be read separately.

The local public roundtrip explicitly reused the exact complete183 gradient
references after checking every original input, phase report and current math
source hash. It records **zero fresh gradient cases** and8362 freshly evaluated
unit-domain endpoints, with actual natural terminal0 and unchanged sources.
Fourteen controls reject reduced/wrong scopes, missing/corrupted/truncated
parts, path escapes, substituted progress bytes and nonfinite/nonunit phases.
An exact unit-circle positive control also passes. Reproduce the controls
after a completed restoration with:

```text
python -B tools/cooperative-stable-replay/test_phase183_evidence_controls.py --packet strict/validation/cooperative-Python183-complete-phase-20261017 --restored new-Python183-phase-replay/restored --output new-Python183-phase-replay/actual-evidence-and-domain-negative-controls.json
```

This evidence checks actual saved phase endpoints. Intermediate power and
interference feasibility, every inner iterate, QT/MC/outer trajectories,
original solver dual/KKT proof, global optimality and original-reference/full-
paper agreement retain their separate requirements. Existing complete final/QT
and configured channel-moment packets keep their own scopes.

The included parent-ff77c3d receipts bind all26 files read separately from
GitHub, all10 successful checks and two downloaded fresh M72 CI artifacts.
Each of those parent jobs checked1152 states/7680 scalar fields per precision;
neither receipt is presented as a result for this new phase CI job.
