# Cooperative multi-satellite and multi-RIS: Fig. 4/5 axis and saved-value evidence

## Scope and source identities

The published paper is *Cooperative Multi-Satellite and Multi-RIS Beamforming: Enhancing LEO SatCom and Mitigating LEO-GEO Intersystem Interference*, DOI 10.1109/JSAC.2024.3460068, IEEE JSAC 43(1), pp. 279–296. References to pages below are to the final publisher PDF supplied by the author. The user also supplied an author working archive, `test_varsigma_316.zip`; the archive and its original files are not redistributed here. Its SHA-256 is `82c6986e020995f4359056e7ad64aaddb6c86cfe8471ceced88914958780c0ba`.

These sources expose an axis-label inconsistency and a configuration discrepancy. They do not establish the exact scripts, random seeds, initialization or averaging population used for the published curves.

## Interference threshold and noise normalization

The final paper, p. 283, Eq. (7), defines the threshold ςₖ as the upper bound on aggregate interference power received by GEO terminal k. On pp. 291–292, Figs. 4 and 5 label the horizontal axis `ς (W)`, while marking the ITU level `I/N = −12.2 dB` near 0.06 on that same axis.

In the supplied ZIP:

- `test_varsigma_316/main.m`, line 14, sweeps `test_variable=0.01:0.01:0.12`.
- `test_varsigma_316/INIT_S_AO_beta_N_100_SCSI_u2_k1_j2.m`, lines 257–259, set `T_cs=235.3`, `B_u=100*10^6`, and `k_b=1.380649*10^(-23)`. These imply the script's common noise reference N = k_b B_u T_cs = **3.248667097 × 10⁻¹³ W**, or approximately −94.883 dBm.
- The same INIT script, lines 342–343, divides the LEO-to-GEO channel power gain by N; lines 538, 681 and 685 form the resulting normalized interference quadratic and constrain it by `varsigma(k)`; line 531 sets `varsigma(k)=test_variable`.

Under precisely this script's shared-noise convention, the equivalent physical interference threshold is **I_limit(W) = varsigma × N**. Values 0.01, 0.06 and 0.12 correspond to approximately 3.24867 × 10⁻¹⁵, 1.94920 × 10⁻¹⁴ and 3.89840 × 10⁻¹⁴ W, respectively. The annotated ratio 10^(−12.2/10) ≈ 0.060256 is consistent with a normalized axis near 0.06. If 0.06 were instead interpreted literally as 0.06 W under the script's noise reference, I/N would be about +112.66 dB, not −12.2 dB. Thus the printed W label conflicts with the author-script normalization and figure annotation under that convention; the exact published plot-generation normalization is not independently established.

The final paper's Table I, p. 291, lists `k_B T_R B_W = −94 dBm` under the label “noise power density.” A value in dBm is a power value; −94 dBm corresponds to approximately 3.98107 × 10⁻¹³ W, about 0.883 dB above the script's calculated value. The two values must not be silently substituted for one another when reporting a watt conversion. The exact noise reference used for the published plots remains unverified.

## User count and geometry

Table I, p. 291, reports **U=2, K=1**; the simulation description on p. 290 says that Table I applies unless otherwise stated and that one LEO user is co-located with the GEO terminal. The user explicitly confirmed that **Fig. 4/5 used six LEO users**. The supplied working script `test_varsigma_316/INIT_S_AO_beta_N_100_SCSI_u2_k1_j2.m`, lines 12–14, sets **J=3, K=1, U=6**; its user positions at lines 52–60 place the third LEO user at the GEO terminal's location. These dimensions are set in the INIT script, not in `main.m`.

The user confirmation and existing working script support a six-user reproduction, while the final table specifies two users. Preserve the published-table and author-confirmed configurations distinctly and disclose the discrepancy. The present evidence does not prove the precise source revision or configuration used to generate every published figure.

## Saved Fig. 4 values: a partial reference connection

`test_varsigma_316/plot_record0120.mat` in the supplied ZIP contains `plot_record`, a real 18 × 20 × 5 array; the MAT member SHA-256 is `2c8340da0750f484fbb8b565d6f158406353918879982352a180ae8805acdcb7`. The verification entry point [check_cooperative_saved_fig4_triplicate_means.py](../../../tools/check_cooperative_saved_fig4_triplicate_means.py) reads this archive without extracting it and compares the arithmetic means of three saved rows against existing **author-thesis EPS vector references**, not a newly digitized final publisher PDF. The existing native-24 comparison report has SHA-256 `59f27838ccf3b129348a74ebfcdc85f45f2035e1c2dc35483f470443da7822b7`.

For slice 2 and columns 1–12, the following direct ordinal comparisons require no fitting, interpolation or rescaling:

| Fig. 4 method | One-based MAT rows averaged | Maximum absolute difference from EPS | Points within half an EPS ordinate step |
|---|---:|---:|---:|
| AP-AO | 1–3 | 1.44066 × 10⁻⁵ | 12/12 |
| MR-S-PA | 4–6 | 1.47846 × 10⁻⁵ | 12/12 |
| MR-TTS-PA | 7–9 | 1.21161 × 10⁻⁵ | 12/12 |

The private continuation receipt `ACTUAL_COOPERATIVE_SAVED_FIG4_TRIPLICATE_MEANS_20261030_V1.json` transcribes the first read-only run’s observed standard output; it is not a retained raw stdout file. The original ZIP is not included in this repository.

The existing EPS calibration uses a linear ordinate range 0–14 across 421 coordinate units and a 0.001 coordinate step, giving a full ordinate step of approximately 3.32542 × 10⁻⁵. All 36 comparisons fall within half that step. This is strong consistency with the three saved-value means, subject to the calibration; it does not prove the saved array was the source of the final publisher artwork or that its three entries are independent Monte Carlo runs. `main.m` currently specifies `Experimient_Times=0:2:2` at line 6, which does not establish how the three rows in the saved MAT were produced. No inference is made for other methods or Fig. 5.

The existing MATLAB/Python 24-point results, their original-reference failures and all failed or unresolved outcomes remain intact. This partial evidence is **not** full-reference agreement, dual-language correctness, feasibility, convergence, or whole-paper acceptance.
