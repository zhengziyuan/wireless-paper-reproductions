# Complete ISAC source, input geometry and saved-state diagnostics

The replay verifies the supplied evidence and retains the failed literal LoS
geometry condition. It does not run an optimizer, recover the author's hidden
inputs, certify complete performance curves or pass the six-paper goal.

Run from the repository root with Python 3.12 and the dependency in
`requirements.txt`:

```powershell
& tools/local-runtime/activate.ps1
python -B tools/isac-source-geometry-audit/replay_full_evidence.py --output-dir E:/paper-reproduction-data/isac-source-geometry-fresh-replay
```

Choose a fresh output directory. The default input is
`strict/validation/isac-full11200-source-geometry-20261018`. Every archive part
and member is size/hash checked before restoration. All old epochs are retained.

| Complete scope | What the replay actually checks |
| --- | --- |
| 11,200 scene records | Every original case and 100-channel slot, full BR/RB ray coordinates and complex path gains, source lineage, both array dimensions, initial support and exact shadow-neighborhood bounds |
| 23,900 first BU/RU ray pairs | All six direction coordinates, every source alias, exact closest-line Gram equations, cross-product certificates and MP80/MP100 distances checked against MP120 |
| Four saved No-RIS states | Two full source variants per state, freshly formed H/G/B/C/F/received-signal matrices in MP80 and MP100, every field coordinate and metric checked against sealed complete reports |
| 32 invalid controls | 17 support/geometry/precision/scope controls, nine complete-field/saved-state/scope controls and six archive/transport controls |

There are 322,600 primitive coordinate observations, 1,100 exact bridge-input
groups and 3,700 exact first-user direction-pair groups. Aliases across power,
rotation and trade-off points remain explicit; they are not extra independent
channel draws. The four No-RIS states contain 61,056 field coordinates per
precision. All 96 complete field matrices are freshly evaluated, while original
optimizer histories and native Monte Carlo streams are not regenerated.

The initial-support finding is 6,279 zero-path scenes, 4,542 one-path scenes and
379 two-path scenes. A zero-path bridge remains zero in the certified local
rotation neighborhood. BS rotation can leave that neighborhood, so this finding
does not establish the cause of a failed optimizer or its final support.

Under the literal interpretation that each first BU/RU path reaches the same
user by LoS propagation, all 23,900 supplied ray pairs fail the necessary
common-point condition. Their supporting-line distances range from
0.00054214732989308849 m to 9.998167726835682 m. The original iid angular
numerical recipe is retained. The default replay does not invent user positions
or silently replace the source model. The disclosed 1e-8 m diagnostic scale is
not a paper-specified feasibility tolerance.

The supplied R1 describes disabling RIS-assisted paths; public arXiv v2 names
only RIS-user paths. Both interpretations are replayed at the same actual
W/theta/rotation state, with both the saved iota and a fresh analytic iota.
Communication results agree exactly between variants; sensing can differ.
These comparisons are not newly optimized performance results. The current
all-assisted removal is not proved erroneous against the broader supplied R1
wording.

The complete numerical functions for exact support, exact Gram geometry and
physical metrics are preserved from the closed local audits. The physical
reference is `tools/isac-line-search-replay/mp_physical_reference.py`, with its
actual source SHA bound by `physical_states.py`. No production core evaluator
is called.

Public geometry replay uses the complete supplied primitive vectors and gains.
It reads two complete scenario files for the four No-RIS states. The previous
local audit of all 11,200 complete optimizer input files has separate receipts;
the default public replay does not claim to re-read all those unrelated fields.
Author/publisher document metadata is checked without fetching or redistributing
the full manuscripts, figures or source archives. Final publisher-text
equivalence, original hidden inputs, dual-language performance and full-paper
reproduction remain open.
