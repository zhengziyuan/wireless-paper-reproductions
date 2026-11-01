# Actual dual-language positive-Wick endpoint replay

**Complete native183 execution, original-reference agreement and full paper
reproduction remain false.** This packet reuses saved original numerical
states; it does not rerun a completed Python183 bank or change old flags.

The two retained full-size reporting failures are cases056 and065, with46
and45 phase endpoints. Every endpoint retains J3/U2/N16/M45/K1, complete
complex channel coefficients, its original phase/power/precoder context,
and its original smoothing parameter. AP keeps its individual-user SINR;
MR keeps the original soft minimum and full squared interference penalty.

The non-subtractive conditional/Wick formula is now used by the production
MR phase evaluator in both languages. It preserves all original physical
terms and angular derivatives. No phase is normalized, covariance clipped,
budget reduced, endpoint selected or reference fitted. See [the exact
model identities and implementation scope](../../cooperative-satcom/POSITIVE_WICK.md).

| Actual complete91 check | Python | MATLAB |
| --- | ---: | ---: |
| Complex gradient coordinates checked | 8190 | 8190 |
| Maximum gradient error against retained MP80 | 5.212242534e-11 | 5.838949278e-11 |
| Maximum criterion error against retained MP80 | 1.466066174e-13 | 2.531880278e-13 |
| Maximum complete gradient norm | 9.988172295e-7 | 9.988172295e-7 |

Every component passes the unchanged absolute1e-9 plus relative1e-10 field
policy. Every full gradient passes the original strict1e-6 norm threshold.
Comparisons use Decimal110 arithmetic on stored binary64 outputs and the
retained complete MP80 strings. These are finite-precision comparisons,
not outward interval enclosures or a global-optimality claim.

The first native replay returned83 endpoints and retained8 transport errors:
MATLAB could not divide a vector by a MAT-file integer smoothing scalar1.
The entry now converts that scalar exactly to double1. The complete91
production-provider replay then passed without changing an input value.
The exact scalar non-Gaussian witness, original full-dimension finite
differences and original increment checks pass as separate controls.

## Retained complete183 bank

The original Python183 bank contains all8 schemes per point,8362 saved phase
contexts,6163 QT candidates and183000 actual channel-moment draws. Its old
independent float auditor passed181 points and failed cases056/065. All183
retained nonphase physical/matrix/QT/RNG checks pass. The retained MP80
summaries report no false endpoint norm stop, but their whole-case flags
remain false. The new91-endpoint replay does not rewrite those flags or
claim a complete historical inner-trajectory replay. The complete183 raw
bank remains external; this public archive contains the actual91 endpoints.

A new full183 MATLAB attempt with the checked phase formula retained8 early
AP QT solver failures. It was stopped for diagnosis; no failed point is a
successful native figure. Native solver conditioning and original curves
remain open. This is separate from the verified phase arithmetic repair.

## Reproduce the saved numerical checks

Install `strict/requirements.txt`. The15.27 MB archive contains the complete
91-input MAT fixture, retained MP80 reference values, actual native outputs
and their summary. It excludes private paths, manuscripts, solver binaries
and credentials. Each numerical payload is checked separately after archive
verification. The published archive SHA256 is
`1cb56dd63f86613e6436c456cbf76bfe6c151c6410b0956f9a07e55281e199cc`.

Git stores the same archive in bounded transfer parts plus
`native91-positive-wick.tar.gz.parts.json`. The unpacker verifies each part,
joins them in memory, verifies the unchanged complete archive SHA and then
checks all four numerical payloads. The commands below also accept the
original complete archive when it is present; numerical bytes are identical.

```text
python tools/cooperative-stable-replay/unpack_evidence.py --archive strict/validation/cooperative-positive-wick-20261017/native91-positive-wick.tar.gz --expected-sha256 1cb56dd63f86613e6436c456cbf76bfe6c151c6410b0956f9a07e55281e199cc --output-dir new-cooperative91
python tools/cooperative-stable-replay/audit_saved_components.py --fixture new-cooperative91/inputs/original-all91-inputs.mat --references new-cooperative91/inputs/references.json --native-dir new-cooperative91/native --output new-native91-audit.json
python tools/cooperative-stable-replay/audit_saved_components.py --fixture new-cooperative91/inputs/original-all91-inputs.mat --references new-cooperative91/inputs/references.json --output new-python91-audit.json
```

These commands independently check the actual saved native values on a host
without MATLAB. A fresh MATLAB arithmetic replay uses
`replay_saved_native(fixturePath,newOutputDirectory,fixtureSHA256)` from
`tools/cooperative-stable-replay`, with the production package on its path.
It requires no CVX solve. Full native optimization uses the original external
CVX dependency and remains distinct from saved-output checks.

The full per-coordinate Decimal110 audit reports are retained losslessly as
`actual-native91-audit.json.gz` and `actual-python91-audit.json.gz`. Their JSON
summaries give compressed and original byte hashes. Every8190-coordinate
report can also be regenerated from the complete public numerical inputs.
