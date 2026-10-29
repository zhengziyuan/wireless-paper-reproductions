# First native case: partial implementation and numerical evidence

This package records the completed **first original Hotspot native matrix case** (N=16, K=15, U=1): all 15 row moments at the original 80- and 100-digit precisions, giving 30 complete 16-by-16 matrices retained as exact MP integer-word tuples. The prescribed full moment uses all 15 row terms and all 210 ordered cross-products per precision. Comparison with the saved native matrix passed all 256 complex-field gates and all 512 real/imaginary cross-precision checks at the original checker tolerances.

The object is E[A A^H], where Pi_k=h_k h_k^H/||h_k||^2 and A=I-sum_k Pi_k. Under the recorded independent-channel model, E[A A^H]=I-sum_k E[Pi_k]+sum_(k!=j) E[Pi_k]E[Pi_j]. This identity does not establish that A is the orthogonal projector onto a joint channel nullspace.

## Contents and provenance

- `native-input-words.json`: complete original NHU operands and native composite binary64 words.
- `first-case-projector-values-only.json.gz`: all 30 complete row matrices and opaque historical provenance digests.
- `all256-native-P-components-original-gates.jsonl.gz`: all 256 saved component records, both precision checks and original tolerances.
- `scope-and-results.json`: scoped results and historical preparation metadata.
- `sources/`: ten byte-identical mathematical, cache and comparison source snapshots used by the recorded execution.
- `public-implementation-manifest.json`: exact data/source hashes, execution roles, runtime metadata and explicit omissions.

The source guard is already published at [immutable commit 973d44d](https://github.com/zhengziyuan/wireless-paper-reproductions/blob/973d44d2116d8af01274651b99c5bb9ba33fe75c/tools/hotspot-source-guard-v11/call_only_numeric_source_guard.py) and is not duplicated. Inclusion of a loaded dependency does not certify every function in that file.

## Execution and scientific limits

**This partial evidence release is not a standalone runnable reproduction package.** The historical hosts `compute_first_case_rows.py`, `compare_first_case_composite.py` and `verify_persistent_projector_cache.py` appear only as original execution hashes. They depend on machine-specific source/cache admissions; no portable replacement or standalone verifier was executed for this release.

Private cache-key preimages and complete three-file cache records are absent. The export cannot recompute the old keys or replay the original cache API. The 93 frozen mpmath source files are not bundled; recorded Python/mpmath versions alone do not establish runtime equivalence.

New uncached row moments were actually integrated at the original precisions. Zero new integrations describes only later cached assembly and artifact preparation. MP80/MP100 agreement is not a rigorous quadrature-error certificate.

No full optimizer, physical feasibility, convergence, original-paper reference, all-18-case or six-paper acceptance is claimed.

The unchanged `scope-and-results.json` describes its historical locally prepared snapshot, not live publication status. Actual GitHub commit and full-body readback are recorded separately after publication; this README does not claim an upload has already occurred.
