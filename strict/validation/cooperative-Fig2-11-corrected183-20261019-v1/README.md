# Corrected Algorithm 3: saved183 dual-language performance and Figures2–11

This package contains actual completed results for the existing183 configured cooperative satellite scenarios in Python and native MATLAB. Each case keeps the six unaffected methods exactly and replaces MR-S-TS and MR-TTS-TS with completed corrected Algorithm3 results. It provides **2,928 method rows** (2,196 reused and732 corrected), all ten PNG/SVG figures, **2,064 plotted computed ordinates**, and **1,032 historical author EPS vector ordinates**. It runs no new optimizer or Monte Carlo simulation.

The full183 own-state feasibility, constraint, algorithm and independent high-precision checks were accepted in separate scoped closures. Their source digests are retained here. The original nativeA host exit1, earlier reader failures, and historical17/18 outer-source coverage boundary remain recorded. Acceptance of those completed configured scenarios does not establish agreement with the original paper or complete the six-paper goal.

## Re-render from the public data

Use Python3.12 with the versions in `requirements-render.txt`, then run:

```sh
python -B render_saved_figures_v1.py --output-dir path-to-a-new-output-directory
```

The entry reads only the two bundled JSON data files. It produces ten PNG/SVG figures and the plotted/reference numerical tables. The original plotting function bodies are preserved. `ACTUAL_PUBLIC_JSON_ONLY_FIRST_USE_RENDER_AND_NUMERIC_PIXEL_VERIFICATION_V1.json` records one actual first-use run: all ten PNG pixel arrays and all plotted numerical rows match the saved original render. Different Matplotlib/font versions can affect rendering; first-use verification used Python3.12.14, NumPy2.5.3 and Matplotlib3.11.2.

## What the curves mean

The left panels are genuine historical author thesis EPS vector references. The right panels are the actual corrected saved dual-language results with their own nonnegative vertical range. The historical vector source has not newly been certified as identical to the final publisher figure. Every reference gap is reported without fitting; there is no reference-agreement PASS or confidence interval. Large differences and nonmonotone saved results are visible.

**Figures2/3 still show the existing terrestrial Rician-factor10dB bank as a clearly labelled diagnostic.** The final paper SectionVII opening (PDFp12, printedp290) makes TableI defaults conditional on later statements. On PDFp13/printedp291, the Fig2/3 captions fix satellite factors20/0dB, and the subsequent paired-factor sentences describe both factors20/0dB. Thus terrestrial20/0dB is an executable known parameter correction, not an indefinitely missing author parameter. The opening respectively order has a minor reversal against the captions, resolved by those explicit later paired-factor sentences. The default TableI terrestrial10dB does not override them. The prepared24-case correction plan is bundled; none of those new runs has been started. Since an input changes, all eight methods in both languages and the full1,000-realization checks must be computed for those24 new scenarios. Old six-method values at10dB cannot stand in for them.

Figures4/5/11 retain the source-axis label inW beside the executed normalizedI/N axis. The precise historical executable dimensional convention remains unresolved; no rescaling is fitted. Unreported historical geometry/gains/seeds and numerical budgets remain disclosed reconstruction choices. Configured original algorithms and full existing budgets are retained; an author stopping-cap value is not invented.

## Case mapping and files

| Figure | Existing183 ordinals | Sweep |
|---|---:|---|
|2|0–10|power, satellite20dB; current terrestrial10dB diagnostic|
|3|11–23|power, satellite0dB; current terrestrial10dB diagnostic|
|4|24–35|interference, satellite20dB|
|5|36–47|interference, satellite0dB|
|6|48–56|subsurface count, satellite20dB|
|7|57–65|subsurface count, satellite0dB|
|8|66–80|terrestrial Rician sweep, satellite0dB|
|9|81–95|terrestrial Rician sweep, satellite10dB|
|10|96–110|terrestrial Rician sweep, satellite20dB|
|11|111–182|multi/single satellite, three geometries, satellite0/20dB|

Figure11 keeps its six AP-AO curves and updates its six MR-TTS-TS curves. Figure1 is a system diagram; TableI lists parameters rather than numerical result rows. Figure12 is delivered separately. Figure13 is a separate live original timing workflow and is untouched here.

`all183_dual_corrected_performance_six_reused_two_TS_replaced.json` contains every original numerical evaluation field. Private paths were replaced by source IDs; source digests and byte lengths remain. `original_assembly_SHA256` identifies the original local assembly artifact; it is not the public projection digest. `MANIFEST.json` identifies the public bytes. `SOURCE_PROVENANCE_AND_PORTABLE_PROJECTION_V1.json` retains the actual consumed input identities. No private paths, raw state tapes, individual MP operands or runtime caches are bundled.

See the [corrected Algorithm3 implementation](../../../cooperative-corrected-Algorithm3/README.md) and the adjacent scoped183 verification evidence. The figure source mapping and unfitted reference-gap JSON retain the scientific limits. **Original-reference agreement and full-paper reproduction remain unpassed.**
