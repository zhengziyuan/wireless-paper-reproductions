# First native case: partial implementation and numerical evidence

This package records the completed **first original Hotspot native matrix case** (N=16, K=15, U=1): all 15 row moments at the original 80- and 100-digit precisions, giving 30 complete 16-by-16 matrices retained as exact MP integer-word tuples. The prescribed full moment uses all 15 row terms and all 210 ordered cross-products per precision. Comparison with the saved native matrix passed all 256 complex-field gates and all 512 real/imaginary cross-precision checks at the original checker tolerances.

The object is E[A A^H], where Pi_k=h_k h_k^H/||h_k||^2 and A=I-sum_k Pi_k. Under the recorded independent-channel model, E[A A^H]=I-sum_k E[Pi_k]+sum_(k!=j) E[Pi_k]E[Pi_j]. This identity does not establish that A is the orthogonal projector onto a joint channel nullspace.

## Contents and provenance

- `native-input-words.json`: complete original NHU operands and native composite binary64 words.
- `first-case-projector-values-only.json.gz`: all 30 complete row matrices and opaque historical provenance digests.
- `all256-native-P-components-original-gates.jsonl.gz`: all 256 saved component records, both precision checks and original tolerances.
- `scope-and-results.json`: scoped results and historical preparation metadata.
- `sources/`: ten byte-identical mathematical, cache and comparison source snapshots used by the recorded execution.
- `public-implementation-manifest.json`: unchanged historical data/source hashes, execution roles, runtime metadata and explicit omissions.
- `verify_portable_saved_first_case.py`: portable saved-evidence verifier using the original published full-moment function and comparison gates.
- `portable-saved-verification-summary.json`: sanitized summary and receipt commitments for the later actual saved-evidence verification.

The source guard is already published at [immutable commit 973d44d](https://github.com/zhengziyuan/wireless-paper-reproductions/blob/973d44d2116d8af01274651b99c5bb9ba33fe75c/tools/hotspot-source-guard-v11/call_only_numeric_source_guard.py) and is not duplicated. Inclusion of a loaded dependency does not certify every function in that file.

## Run the saved-evidence verifier

Python and `mpmath` must already be available. From this package directory, run:

```sh
python -B verify_portable_saved_first_case.py --package-dir . --output ../portable-check.json
```

Choose a new output JSON in an existing directory; existing files are not overwritten. Keep the usual `package/sources` layout at least two directories below the filesystem root. The verifier pins the four input files and six original source modules, decodes all 30 saved matrices from exact MP integer words, checks all 15 x 512 row components, reassembles the full moment at MP80/MP100, and applies the original 256 native-complex and 512 real/imaginary crossprecision gates. It also compares exact native/reference tuples and complete comparison records with the saved historical evidence. It performs zero integrations or optimizer calls and writes one JSON capped at 64 KiB, without input/source copies or a cache. External resource protection remains the caller's responsibility.

The recorded actual run used **explicit paths to the existing source/data files**, not the `--package-dir` command above. On CPython 3.12.14 with mpmath 1.4.1, it exited naturally with code 0 after 6.656 seconds. All 7,680 row checks, 256 native complex checks and 512 composite crossprecision checks passed. At each precision the unchanged function retained all 15 row terms and 210 ordered cross-products. All 256 historical native/reference tuples and complete comparison records matched exactly. No new row integration was performed. Source/input intervals were unchanged; the full retained run occupied 78,314 bytes including private guard receipts. The public summary separates these results from source and runtime provenance.

## Scientific and provenance limits

**This is a runnable saved-evidence check, not a standalone full-paper reproduction.** The historical hosts `compute_first_case_rows.py`, `compare_first_case_composite.py` and `verify_persistent_projector_cache.py` remain represented only by original execution hashes. They depend on machine-specific source/cache admissions; the portable verifier does not replay those admissions.

Private cache-key preimages and complete three-file cache records are absent. The export cannot recompute the old keys or replay the original cache API. The 93 frozen mpmath source files are not bundled; recorded Python/mpmath versions and matching saved outputs do not establish historical runtime byte equivalence.

New uncached row moments were actually integrated during the original production at the original precisions. Zero new integrations describes later cached assembly, artifact preparation and this saved-evidence verification. MP80/MP100 agreement is not a rigorous quadrature-error certificate. No full optimizer, physical feasibility, convergence, original-paper reference, all-18-case or six-paper acceptance is claimed.

The unchanged `scope-and-results.json` and `public-implementation-manifest.json` describe the original historical snapshot. They are not rewritten to inventory this later verifier and summary. Full private receipts include machine paths and are retained locally; their SHA256 commitments appear in the sanitized summary. Publication status and remote readback are recorded separately.
