# Complete Python U6 Fig4/5: 24 saved points and unfitted EPS comparison

This draft contains both twelve-point Python axes (kappa_N = 20 and 0 dB), all eight original methods, kappa_R = 10 dB, and all six saved user SINRs per method. It reuses the 23 completed producer/scientific summaries and the originally closed first point; no optimization, MP, MC or new input generation was run for this collection. Each new result's recorded JSON, exact configuration and original held producer journal is bound to its completed three-stage scientific summary. The first point's four-stage closure is reused explicitly. The native continuation is independent and no native completion or PASS is inherited here.

The CSV has 192 point-method rows with original EPS vector coordinates, nominal ordinal, historical mapped reference minSINR, actual Python minSINR, signed/absolute/relative gap, gap in full EPS coordinate steps, and source/science-binding digests. JSON preserves all six actual user values and the complete per-method/axis max and RMS diagnostics. No reference values are replaced by old reproduction data. EPS quantization steps are full vector-coordinate resolutions, not confidence intervals or author measurement error bounds.

**The historical reference gate remains false.** Pairing is by the fixed ordinal .01:.01:.12 grid. The reconstruction's horizontal parameter is normalized INR, while the historical EPS horizontal label uses W; ordinal pairing does not establish their unit mapping. No scaling, fitting, interpolation or hidden unit conversion is applied. The author's optimized performance averaging population, cached W and random initial phase have not been recovered. The audited 1000 channel draws (fresh per family or explicitly same-input reuse) validate channel moments; they are not 1000 optimized performance replicates. Closed ownstate/stop/QT/phase science does not establish historical curve agreement or full-paper acceptance.

The source protocol is the author-confirmed U6 scene with the stated reconstructed numerical controls. These are complete actual Python axes, not a dual-language or original-reference success. Local path metadata is projected to source labels; numerical fields, MP-summary identifiers and CSV binary64 values are unchanged. This packet contains saved scalar evidence only, with no new runner. A downstream plot can directly use the original EPS and Python columns while retaining the axis and population qualifications above.


## Actual saved-scalar scientific diagnostic plots

`Fig4_Python12_all8_unfitted_original_EPS_diagnostic` and `Fig5_Python12_all8_unfitted_original_EPS_diagnostic` are provided as PNG and vector PDF. They were actually generated from the sealed 192-row CSV and both PNGs were visually inspected. Each main panel preserves all eight methods: solid filled markers are actual Python values and dashed open markers are original historical EPS values. Each lower panel shows the signed Python-minus-EPS gap. The horizontal coordinate is explicitly paired ordinal 1–12; the W-to-normalized-INR mapping remains unverified. The reference gate is not passed. These are diagnostic displays of the saved values, with no fitted line or conversion of units.

`plot_saved_python24_unfitted_Fig4_Fig5_v1.py` is the exact script used for these actual plots. It requires Python and Matplotlib, checks the sealed CSV digest, rejects missing/nonfinite or unbound rows, and writes only plots. To reproduce into a fresh directory from any working directory:

```text
python plot_saved_python24_unfitted_Fig4_Fig5_v1.py --output-dir /your/fresh/plot-directory
```

Supply the script's package path if running elsewhere. Existing plot files are never overwritten. No optimization, MP or MC is executed by the renderer. In particular, the actual1000 channel-moment samples do not mean1000 independently optimized performance repetitions. The original three numerical JSON/CSV files have unchanged bytes after plotting. Both original-reference and full-paper acceptance remain false.
