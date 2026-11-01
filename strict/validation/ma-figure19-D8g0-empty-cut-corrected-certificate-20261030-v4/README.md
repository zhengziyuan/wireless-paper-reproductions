# One saved Fig. 19 certificate: exact empty-cut correction

This package documents a corrected independent certificate check for one saved Python point: Fig. 19, D = 8, realization 0, N = 4, M = 3. The recorded run passed both MRT and ZF partition-and-bound gates. It reused the saved search certificates and ran no optimizer, Monte Carlo experiment, or new search.

| Recorded check | MRT | ZF |
| --- | ---: | ---: |
| Feasible unordered antenna sets covered exactly once | 446,421 | 446,421 |
| Independently evaluated unpruned leaves | 31,467 | 36,227 |
| Saved prune bounds independently checked | 28,921 | 28,039 |
| Prunes with exactly zero feasible completions | 59 | 58 |
| Feasible sets accounted for by prune subtrees | 414,954 | 410,194 |

Both modes returned the saved zero-based winner `[15, 25, 47, 57]`. For this point, the original conservative uniqueness test also passed. The guarded run exited naturally with code 0 in 220.672 seconds, closed its source/input identity interval, and retained 39,728 bytes in total. `saved-verification-summary.json` records the mode checks and commitments to the original local report and guard receipt. The old failed report remains preserved. The other 148 similarly classified failed points have not been rechecked by this run.

## What was corrected

The independent reader previously required every saved cut to have a positive number of feasible completions. Having at least r residual vertices does not establish that their compatibility graph contains an r-clique. An otherwise valid cut can therefore have exactly zero feasible completions.

The versioned adapter replaces exactly one assertion in the frozen reader:

```python
need(amount > 0, 'Empty feasible cut')
```

with an exact nonnegative-integer requirement. An inverse AST comparison ensures that the rest of `certify_partition` is unchanged. A zero cut contributes zero to coverage, while remaining in the original prune counters, supplied-cut reachability checks, and cut commitment. Its exact upper-bound digest and comparison against the earlier independent leaf incumbent must still pass. Coverage, traversal counters, exact best product, saved winner, and conservative uniqueness checks are retained. No tolerance, objective, search, or experimental budget was changed. This was a defect in the reproduction's validation reader; it is not evidence of an error in the original paper.

## Reusable code and regression evidence

`verify_saved_ma_empty_cuts_v4.py` and the byte-identical `verify_one_closed_python_grid_prune_trie_compact_v2.py` are included. The frozen reader is retained as historical source; use the adapter for the corrected path. The actual nine-test synthetic receipt is `synthetic-regression.json`. It includes the valid zero-completion example and rejection tests for a bad upper digest, an unsafe upper bound, wrong counters, a wrong winner, an unreachable cut, and negative or noninteger cardinalities.

From this directory, the small standard-library regression can be reproduced with a fresh output filename:

```text
python -X utf8 -B verify_saved_ma_empty_cuts_v4.py --frozen-reader verify_one_closed_python_grid_prune_trie_compact_v2.py --expected-frozen-reader-sha256 30d26f1d1198566ef1dc36babc210e822371006a2cd8671b7016e085f0d8a7fe --synthetic-regression --synthetic-output synthetic-regression-local.json
```

The recorded regression used the original explicit file paths. The command above is documentation for the same source interface; no additional run from this publication directory is claimed. Preserve exact file bytes: the adapter checks the frozen reader's length and SHA-256, and this directory's attributes disable line-ending conversion for Python and JSON files.

The actual certificate path also uses NumPy and two already published, unchanged dependencies:

- [Certificate framing and independent bounds](../ma-figure20-D3g0-N6-actual-theory-certificates-20261019-v1/sources/certificate_helpers.py), SHA-256 `39e55c5e3b8ba7b20433638db16189e7ab3f993c775ffa451f527a6376913d45`.
- [Independent rational/cofactor kernel](../ma-figure19-D3g1-exact-global-grid-20261020-v1/verify_all126.py), SHA-256 `40a93a0ff9afb77302191d5de729af2f0fe2fbd5d0590cdac09eadf656cfacf1`.

Both complete public bodies were compared with the local inputs used by the recorded run. They are referenced, not copied. The manifest records immutable public references and exact identities.

## Scope and unavailable replay inputs

This compact package contains source and a summary of an executed check. The D8/g0 job, typed bindings, checkpoints, and original certificate frames are retained locally and are not included. Consequently this package alone cannot independently replay the D8/g0 proof; the synthetic regression does not substitute for that proof. File commitments identify the retained evidence but do not replace access to its contents. An actual saved-data invocation requires the complete input set, a new source-pinned local plan, and an external resource guard.

The proof establishes a discrete global winner for the inherited typed numerical operands and the selected theoretical candidate objectives (MRT Eq. 13 and ZF Eq. 39). The lower-cost theoretical choice was explicitly selected by the user; the author's historical search protocol has not been established. It does not establish symbolic exactness of transcendental inputs, continuous-position optimality, or physical/reference correctness. The historical full branch-event digest is unavailable. N = 6/M = 5 Fig. 20 requires a separate reader.

Native MATLAB agreement, original-paper reference agreement, all 2,600 Fig. 19/20 points per language, and the full-paper gate remain unpassed by this artifact. The original experiment budgets remain required, including 1,000 final saved fading evaluations and the original MA/FPA budgets. This certificate-only check neither completes nor reduces them.
