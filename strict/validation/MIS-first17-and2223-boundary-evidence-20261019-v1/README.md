# Saved MIS boundary and roundoff evidence: two finite scopes

This package preserves one actual Fig11 communication start and a separate sensing start2223 diagnostic. It contains saved numerical inputs, results, archived independent reports, and a finite reader. It is not a completed figure, a full trajectory certificate, or an original-author reproduction archive.

## Two stationarity measures remain separate

For the first Fig11 MIS start, all17 captured fixed-μ returned states satisfy the independently evaluated **implemented closed-simplex projected KKT** threshold1e-6 and the domain checks. None of the17 satisfies the **printed-form row-mean gradient** comparison at that same implementation-selected value. The row-mean norms are23.467267108279692–23.467267292073526; projected KKT norms are5.367409534115203e-7–9.976719366170244e-7. The two residuals differ at boundary schedules. These17 states must not be called stationary under the printed open-simplex criterion.

This distinction is already disclosed in [the implementation README](../../mis-communications/README.md) lines11,55,57,59 and [COMM_ERRATA](../../mis-communications/COMM_ERRATA.md) lines75–80. Author-supplied finalR2 source, SHA256`6e27fb9fd2ba0decc9d7bcfc54bcb73612553f91f6df923ab502e7d561058cb0`, Algorithm1 line619 says only “is above the threshold”. It supplies neither an epsilon symbol nor a numerical threshold there. The positive schedule domain is at396–400, row-mean projection523–533, and main-text retraction/projection reference592–600. The formula at1029 is inside a commented1024–1030 block and is **not printed Appendix evidence**. The private manuscript is excluded. Publisher-final-PDF equivalence is not established here.

The6000 starts,4000 RCG cap,1e-6 threshold, five initialμ values and terminalμ.001 are disclosed reconstruction controls. They are not numerical budgets reported by this communications paper. The separate sensing run uses its original saved30-outer/4000-inner settings; do not transfer the communication threshold interpretation to its scheduled inner tolerances.

## Fig11: capture complete, strict numerical comparison retained false

The actual first start has17μ input/return pairs. All102 typed arrays are provided as safe NPZ, with dtype/shape/F-order IEEE digests and JSON event metadata. The original first-start gzip includes its final state and complete scalar inner histories. The original typed pickle is not distributed. Capture readback passed97 checks, including every adjacent state link and final-state serialization. A first reader's integer100 versus float100.0 metadata error remains archived; its corrected reader compares μ binary64 values without changing arrays or producer controls.

The independent reference uses binary64-reconstructed geometry followed by unchanged Decimal60 field sums, LSE, phase derivatives and simplex projection. Geometry is not claimed to be MP or separately captured. LSE objectives agree for17/17, and the final binary score agrees exactly. The original5e-13 KKT scalar-comparison gate passes12/17 and fails stages11,12,13,14,16 (zero based), with maximum error4.556562027440167e-12. Its false gate is retained. In two saved-state diagnostics (stages12 and16), the frozen evaluator reproduces saved KKT exactly; changing only LSE weights to Decimal60-reference weights reduces the discrepancy to about1.45e-16 and1.38e-16. Those counterfactual weights are diagnostics, not installed corrections or original producer results. This is a floating-point summation/weight observation, not a newly established paper error.

## Sensing2223: a new successful return does not erase the old failure

The original saved first outer solve has66 scalar records and ends `corrected_curve_search_exhausted`, KKT0.07674046446744565 above its0.001 tolerance. A separately labeled, single new original-budget diagnostic did not reproduce that failure: all30 outer iterations returned;3113 curve calls succeeded. Settings and configuration match. Stored scalars and flags agree through iterations0–32; iteration33 objective differs by one binary64 ULP (−2.7755575615628914e-17), then paths diverge. The new first outer solve has2689 records. No old failed iterate or failed trial operands were recovered. A specific JIT, BLAS or observer cause is not established.

The new final state alone passed13 source/input/physical/KKT checks. Steering was reconstructed atMP80/100, then field and Lagrangian derivative contractions used binary64 and the simplex projection Decimal60. This is not full-MP gradients or every-outer-state validation. Independent minimum relaxed and binary SINR are47.1428119805848; KKT1.1670064710217553e-6 passes the saved1.2589254117941667e-6 tolerance. The old2223 failure and the original population's720 retained false outcomes remain unchanged.

## Finite reader and dependencies

Install NumPy and mpmath in your chosen environment. All paths below are relative to this directory; use a fresh output path. The three frozen sources are exact copies, with mappings in PROVENANCE. No optimizer, initialization, random draw, producer or full-bank replay is invoked by these reader modes.

```text
python -X utf8 -B read_saved_evidence_v1.py --mode inspect --output /your/data/inspect.json
python -X utf8 -B read_saved_evidence_v1.py --mode fig11 --output /your/data/fig11.json
python -X utf8 -B read_saved_evidence_v1.py --mode roundoff --output /your/data/roundoff.json
python -X utf8 -B read_saved_evidence_v1.py --mode sensing2223 --output /your/data/new2223.json
python -X utf8 -B read_saved_evidence_v1.py --mode trace --output /your/data/trace.json
```

`fig11` returns2 when any original strict comparison remains false; it must not hide the five retained failures behind the implemented-threshold pass. Other modes report only their finite scopes. Different numerical libraries can expose roundoff differences; none may be used to overwrite the archived reports. The path-adapted public reader has now had one actual finite first use of all five modes, with unchanged reader/source/fixture bytes: inspect0, fig11**2**, roundoff0, sensing2223 0, trace0. The Fig11 exit2 is a real retained strict-comparison failure, not a successful scientific exit. A separate output readback confirms17 implemented-KKT/domain passes,0 printed-form passes at the selected1e-6 value, exactly the same five strict scalar-comparison failures, trace divergence33, and the new2223 physical certificate. All shared numerical fields match their archived calculations bitwise. See [the actual source interval and exit record](evidence/portable-first-use/root-five-modes.json) and [the independent output readback](evidence/portable-first-use/independent-output-readback.json). The V1 input/source hashes in that record precede this documentation seal; the mathematical sources, reader and fixtures remain unchanged. These finite results do not make the whole scientific scope pass.

The full Fig11 campaign was running at the recorded observation; this package makes no current completion claim. It contains no other starts, measurement archive, private paper, whole-population independent audit, dual-language acceptance, historical-reference agreement, or full-paper PASS.
