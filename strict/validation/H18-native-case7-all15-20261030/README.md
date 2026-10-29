# Native case 7: portable saved-evidence verification

This package contains **one completed Hotspot native matrix case**, with N=16, K=15, U=1 and beta=10. It retains all 30 complete 16-by-16 row-moment matrices at the original 80- and 100-digit precisions. The portable check passed all 7,680 row-component comparisons, 256 native complex-field gates and 512 composite real/imaginary cross-precision gates. All 256 historical native/reference tuples and complete comparison records replayed exactly.

At each precision, the unchanged original full-moment function uses all 15 row terms and 210 ordered cross-products. With Pi_k=h_k h_k^H/||h_k||^2 and A=I-sum_k Pi_k, the recorded independent-channel model gives P=E[A A^H]=I-sum_k M_k+sum_(k!=j) M_k M_j, where M_k=E[Pi_k]. This does not establish that A is an orthogonal projector onto a joint channel nullspace.

## Files and shared dependencies

- `case7-projector-values-only.json.gz`: all 30 saved matrices as exact MP integer-word tuples, with opaque provenance commitments.
- `all256-native-P-components-original-gates.jsonl.gz`: the existing complete component evidence, including native binary64 words, references and original comparison records.
- `public-case7-manifest.json`: input hashes and all 30 original value commitments.
- `verify_portable_saved_case7.py`: the case7 portable entry point.
- `saved-verification-summary.json`: sanitized actual results and private-receipt commitments.

The entry point reuses the unchanged verifier and six original mathematical/support modules in [the first-case package](../H18-first-native-case-all15-20261029). Those files are pinned by size and SHA256 and are not duplicated here. Their source snapshot is commit `8e1450ab018f09adb8d7f7c80789585a2db1984c`; the shared portable verifier was published in `e6084095123a138e375a47ac5a87660ae79e2bb4`. Python and `mpmath` must already be available. No dependency is downloaded automatically.

## Run the saved-evidence check

From this package directory in a checkout containing both sibling packages, specify the existing shared dependencies explicitly:

```sh
python -B verify_portable_saved_case7.py --package-dir . --base-verifier ../H18-first-native-case-all15-20261029/verify_portable_saved_first_case.py --source-dir ../H18-first-native-case-all15-20261029/sources --expected-manifest-sha256 2a63262f497c2a7875fc51538bac63d2085d16f4159a2592784d0b28eafcf4e8 --output ../case7-check.json
```

Use a new output filename in an existing directory. Existing files are not overwritten. Explicit `--base-verifier`, `--source-dir`, `--values`, `--components` and `--manifest` paths are also supported. Output is capped at 64 KiB; external resource protection remains the caller's responsibility.

**The recorded actual run used explicit paths to existing files. The `--package-dir` invocation above was not separately tested.** The recorded explicit-path run used CPython 3.12.14 with mpmath 1.4.1 and exited naturally with code 0 after 5.078 seconds. It independently decompressed and checked all 30 exported value commitments, decoded exact MP tuples, assembled the full moments and applied the unchanged original gates. Source/input intervals were unchanged. The result was 22,887 bytes; the complete retained run, including private guard receipts, was 34,350 bytes. No new quadrature, optimizer or native execution occurred during this replay.

## Boundaries

This is a saved-evidence check for case7, **not a full-paper reproduction or acceptance of all 18 cases or all six papers**. MP80/MP100 agreement and exact replay are not rigorous quadrature-error certificates, optimizer feasibility, convergence or original-paper reference agreement.

A separate prior check recorded 33 Hermitian checks, 33 trace checks and 66 exact PSD checks passing on the saved dyadic matrices. This portable command does not rerun that check, and those necessary constraints do not establish complete physical correctness.

The package contains recorded native P words, not the original NHU operands or full typed native input. It does not reproduce private cache admissions or expose cache-key preimages. Recorded runtime versions and matching results do not prove historical runtime byte equivalence. Original row production did perform integrations; zero new integrations describes this later saved-evidence replay. Private paths, raw input archives and full machine receipts are not part of the public package.
