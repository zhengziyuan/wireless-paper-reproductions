# Native analytical vectors at the 36 saved own-block inputs

This addendum closes the parent package's missing native analytical-vector check for its **36 returned inner-block states only**. It newly executes the original native derivative functions at those saved states; it does not recover historical in-memory vectors. The original input MAT and existing complete MP80/MP100 report are referenced in `scope-and-provenance.json` with published payload/source hashes and are not copied again.

The new native probe returned naturally0 on its original held process handle, with the source/input interval closed. The separate saved-decimal comparison then actually returned0 with its own source/input interval closed. There were exactly36 new native evaluate calls and zero new MP reference, optimizer, update, MC, RNG or line-search-trial calls.

| Native vector | Actual returned blocks | Components per precision | Maximum absolute error, rounded |
| --- | ---: | ---: | ---: |
| W |12|288|1.066e-14|
| theta |12|432|8.592e-15|
| rotation |12|72|2.310e-13|

All792 components at each of MP80 and MP100 pass the unchanged strict absolute bound: complex magnitude less than the exact original binary64 `1e-5`, promoted using `Decimal.from_float`. The complete comparison retains every stored error and MP decimal precision. It compares against the previously saved reference vectors; it does not recalculate a physical or MP reference. The largest actual error across both precisions is about2.30975e-13.

The original native `is_rotation`, `is_response`, `is_channel_base`, `is_channels` and `is_evaluate` functions are extracted byte-for-byte from the parent's frozen native source, original lines44–123. The new top level only loads the closed MAT, follows its36 actual returned indices/methods/calls and original fixed iota inputs, calls that derivative chain, selects the corresponding W/theta/rotation vector and saves typed MAT. It contains no update, initializer, QP, optimizer or random sampler. `source-mapping/` records the exact byte slice, its digest, the existing reference layout and the reversible host-only correction.

The new MAT is preserved whole-byte. MATLAB records each vector's actual class, shape, isreal flag and SHA256 of its real then imaginary Fortran-order binary64 components. The saved comparison verifies those hashes before restoring native shapes and flattening in C order, exactly as the existing MP reference reader did. This also checks compact MAT storage promotion and signed-zero transport; values are not silently repaired.

Two actual host failures remain visible. V1 naturally returned1 at an unsupported MATLAB `computer('endian')` call before input loading or derivative evaluation; the independently prepared V2 only uses the valid three-output `computer` interface and corrects the journal child-field collector. V2's native probe naturally returned0, but its owner then returned1 while importing SciPy before any saved-decimal comparison. The same comparison function subsequently ran once in a separate process with the existing dependency paths. No native probe was repeated for that environment correction. The evidence distinguishes native success, the retained owner import failure and the later actual comparison0.

**The final37 own state is not covered by this vector addendum:** its old MP report stores residual diagnostics but not full reference vectors. No new final-state MP calculation was made. Final joint RCG/PGA stationarity failures, the large W diagnostics, the lack of an author absolute W threshold, original-reference differences, full-six scope and full-paper limitations remain unchanged. The original disclosed reconstruction controls are not reclassified as author budgets. See the [parent native evidence](../README.md) for those boundaries.

This is an evidence supplement, not a newly validated portable launcher. The two executed sources are included whole-byte for inspection and provenance; no new replay/inspect test was created or run during packaging. JSON changes only private path metadata strings; all numeric tokens/types/float64 bits and nonpath decimal strings are preserved. `transport-preservation.json` records the projection checks and distinguishes small derived lifecycle excerpts from whole-source copies.
