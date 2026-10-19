# Cooperative SatCom: corrected saved-state Figure 12 diagnostic

This capsule contains all **192 current derived language points** and all
**96 published vector reference points**, together with the actual PNG/SVG and
a portable display interface. It reports numerical differences honestly. It
does not establish original-reference agreement, equality of independently
optimized MATLAB/Python outputs, or whole-paper completion.

[View the actual diagnostic](figures/Fig12-all192-derived-and-all96-published-unfitted-diagnostic.png)
or open its accompanying SVG. The original image was visually checked for all
four panels, readable labels/legends/disclosures, and unclipped axes.

## What the complete point set means

Four scenes combine multi-satellite or single-satellite geometry with
`kappa_N=0` or `20dB`. Each has 12 threshold labels and two methods, `AP-AO` and
`MR-TTS-TS`, in both languages. The complete assembly contains 96 exactly reused
AP-AO points and 96 corrected Algorithm 3 TS points. There are no missing current
slots. The original source interval closed with 441 named source identities.

Every current row retains its saved per-user SINRs, MP80/MP100 decimal strings,
derived sum rate, stored-float comparison, original-vector ordinate, unfitted
gap and recorded point flags. No failed or mismatched result is filtered out.
`data/summary.json` is an explicitly limited projection of the large assembly
metadata. The data projection removes historical embedded `old_legacy_row`
subtrees and local proof-path fields; proof digests remain. Other private
metadata paths are replaced. It does not alter current numeric row values,
rates, precision strings or flags. The omitted old rows were obsolete pre-correction
diagnostics, not replacements for any of the 192 current points.

The rates use `sum_u log2(1+gamma_u)` from the recorded high-precision own-state
checks. This capsule displays the already derived values; its portable host
does not re-evaluate channels, run MP, invoke an optimizer or recompute rates.
The configured 1000 draws concern channel-moment validation. They are **not**
1,000 separately optimized performance trials or an optimized-performance mean.

## Unresolved comparison and units

The paper labels its horizontal threshold in watts. The completed input banks
use an interference-to-noise ratio. Their shared numeric ticks 0.01..0.12 are
shown with that mismatch explicitly disclosed. A physical `I[W]` to `I/N`
mapping remains unresolved. No unit conversion, curve fit, smoothing or
empirical rescaling was applied to align the curves.

The largest absolute unfitted numeric difference from a published vector
ordinate is 15.336630403244865 bit/s/Hz. It is a diagnostic across the displayed
numeric ticks, not a certified like-for-like physical error while the axis
mapping remains unresolved. The published values were recovered from vector
paths in the final Figure 12; their display precision does not recover the
author's random realizations, seed, raw MC data or an agreement tolerance.

The independently optimized Python and MATLAB corrected-TS outputs also differ
substantially in one pair: case 122, multi-satellite, `kappa_N=0`, numeric
threshold 0.12. Python gives 6.789772668418986 and MATLAB 4.906663603119580 bit/s/Hz,
an absolute difference 1.8831090652994059. The other 95 language pairs differ
by less than 0.000175 bit/s/Hz. This large difference was already present in
the earlier pre-correction saved outputs; it is not established as a consequence
of this Algorithm 3 implementation correction. The cause has not been isolated.
See [the saved-rate comparison](evidence/dual-language-saved-rate-comparison.json).
The stored optimizer trajectories differ despite identical configured budgets;
the cause is not established. Both languages pass their own-state checks, and
the native state passes cross-language physical evaluation. These facts do not
make independently optimized outputs equal. Both language curves, their actual flags, and their differences remain
visible. Original-reference, dual optimized-equality and whole-paper gates
remain false. This package does not classify these discrepancies as a proven
error in the original paper.

## Render the same saved values

Python 3.10 or newer and Matplotlib are required. From this capsule, use a fresh
output directory outside it:

```console
python -X utf8 -B sources/render_packaged_Fig12.py --output ../my-Fig12-display
```

The original renderer retains its exact bytes. The new host changes only its
in-memory input/output directories, supplies byte-identical copies of two
packaged inputs in the fresh output directory, and closes source/input hashes
before and after display. The original renderer keeps every data ordinate and
the unit/MC disclosures. The first actual portable-interface execution returned naturally with code 0,
displaying all 192 saved points and 96 vectors with unchanged sources/inputs.
The new PNG bytes were identical to the prior visually reviewed image. A
nonempty SVG was generated; SVG byte identity is not claimed. See the
[actual first-use receipt](evidence/actual-portable-Fig12-first-use.json).
This closes the saved-data display-interface check, not the unresolved physical
unit mapping, original-reference agreement or optimized dual-language equality.

`SOURCE_AND_ARTIFACT_MANIFEST.json` identifies every file except itself. The
local `.gitattributes` preserves exact file bytes. Private banks, solver tapes,
individual mathematical proof bodies and the authors' PDF are not included.
`undistributed/local-identity-*` metadata denotes unavailable original local
evidence, not files accessible to a reader. The small proof summaries and
hashes define the included evidence boundary; they do not replace those data.
