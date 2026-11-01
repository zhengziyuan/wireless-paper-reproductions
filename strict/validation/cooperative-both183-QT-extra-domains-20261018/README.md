# All original QT before/candidate domains and feasibility

This supplement checks both original183-case populations:6181 native MATLAB
QT updates and6163 Python QT updates,12344 in total. It reads every actual
before/candidate primal coordinate from the complete published MAT tapes.
Every MR coordinate is finite, real and strictly nonnegative; finite complex
AP variables remain allowed. Before and candidate satellite power, ground
interference and positive received-signal denominators pass the original
`1e-5` feasibility tolerance.

The completed full MP100 physical contractions are reused only after exact
input, report and current oracle hashes match. This supplement reports zero
fresh MP100 contractions, zero optimizer calls and zero production RNG or
gradient calls. Its fresh work is the complete binary64 primal-domain check
and the separate before/candidate feasibility comparison. It preserves the
original native/Python populations, dimensions and tolerances.

The full per-update reports remain inside five required512KiB-or-smaller
archive parts. The archive is2553825 bytes with SHA256
`276ec596fea1ced5305712bc3e6020c9ebe9f611ab14ec8685c66ef367ce518f`.
Every part and full report member was separately byte-checked. A public
replay starting from the archive parts of both original input packets closed
with exit0. Both complete newly produced numerical reports are byte-for-byte
equal to the sealed original supplement reports. All per-case rows also
match the two earlier local domain audits exactly.

Twelve invalid-domain/constraint controls are rejected. Positive controls
retain zero MR variables, finite complex AP variables, and feasibility within
the original tolerance. The complete controls and actual terminal receipt
are preserved in the archive.

With Python3.12, NumPy2.5.3, SciPy1.18.1 and mpmath1.4.1, use fresh outputs:

```text
python -B tools/cooperative-stable-replay/audit_both183_QT_domains_v1.py --native-packet strict/validation/cooperative-native183-complete-phase-final-QT-20261017 --python-packet strict/validation/cooperative-Python183-final-QT-20261017 --output-dir new-both183-QT-domains
python -B tools/cooperative-stable-replay/test_both183_QT_domain_controls_v1.py --output new-both183-QT-domains/new-all12-controls.json
python -B tools/cooperative-stable-replay/verify_both183_QT_domain_evidence_v1.py --packet strict/validation/cooperative-both183-QT-extra-domains-20261018 --fresh-domain-output new-both183-QT-domains --output new-both183-QT-domains/actual-evidence-verification.json
```

Optional `--native-restored` and `--python-restored` arguments reuse already
restored complete packets after every payload hash is rechecked. They never
allow a reduced case/update population or substitute numerical operands.

These checks do not establish every original inner iterate, solver dual/KKT
certificates, literal exact objective nondecrease, global optimality,
dual-language curve agreement, original-reference agreement or full-paper
reproduction. The ten existing Python negative minimum-SINR increments
within the original tolerance remain in their original separate evidence.
