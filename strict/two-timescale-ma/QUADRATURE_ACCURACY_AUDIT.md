# Same-integral quadrature accuracy: retained v2 and frozen v3

This is a numerical-integration correction, not another channel, covariance,
Jensen function, optimizer, stopping threshold or reduced Monte Carlo bank.
The exact original-model derivation is in
[CORRELATED_ZF_EXACT_EVALUATION.md](CORRELATED_ZF_EXACT_EVALUATION.md).

## Independently established cause

Actual N=6/M=5 and N=8/M=5 first-position comparisons retained every one of
the configured1000 draws, all5000 conditional moments per channel model,
and all Schur/ZF identities. Aggregated physical metrics agreed. However,
the old unsplit Python adaptive rule failed fixed per-moment tolerances
and understated its reported error in30 conditional cases across those
paired comparisons. The original failed paired-v2 receipts are retained,
not relabelled as passes.

For each of those30 cases, an independent scalar audit imported the exact
binary64 projected eigenvalues and rotated mean energies into mpmath.
It evaluated the **same** positive Laplace integral with50-digit
Gauss–Legendre and80-digit tanh–sinh quadrature. Maximum disagreement
between the two high-precision methods was `4.14116e-50`. Relative to that
fixed-parameter reference, the old Python error reached `3.00718235e-8`,
whereas the old MATLAB values differed by at most `1.70974e-14`. Splitting
the same normalized integral at `.25,.5,.75,.9,.99` reduced the independent
double-precision error to at most `5.55112e-17` on those30 cases.

This reference audits integration on the already projected binary64
parameters. It does **not** certify high-precision channel generation,
QR/eigenvectors, a population expectation, every future covariance or an
interval-arithmetic bound. All30 parameter sets and high-precision results,
the original four raw outputs and two failed paired receipts were
hash-retained before the change.

## Frozen v3 numerical controls

Python and MATLAB now partition the unchanged `[0,1]` transformed integral
at the same five deterministic waypoints, with working relative accuracy
`1e-12`, absolute accuracy `1e-12/scale`, and a500-subinterval safety budget.
These are disclosed numerical controls, not fitted physical parameters.
The original declared accuracy gate remains `1e-9`; the independent paired
comparison remains `rtol=1e-9, atol=1e-10`. Its separate combined-reported-
error check also remains unchanged. Reported quadrature errors are
estimates, **not interval certificates**.

The new independent helper fingerprint is distinct from the frozen MA
optimization-core fingerprint. Fresh source-bound N6 and N8 full1000-draw
Python **and MATLAB** position runs have now actually completed. Independent
paired comparisons passed both the unchanged fixed tolerances and the separate
combined-reported-error checks for all retained per-position moments and metrics:
[N6 paired evidence](../validation/two-timescale-ma-corrected-zf/paired-corrected-position-n6-v3.json),
[N8 paired evidence](../validation/two-timescale-ma-corrected-zf/paired-corrected-position-n8-v3.json).
The fresh Python runs'30 previously problematic moments also passed against the
retained80-digit fixed-parameter reference, with maximum error `5.55112e-17`.
Neither these tests nor the30-point scalar audit is completion of either
300-geometry corrected-source figure bank or historical-curve recovery.

MATLAB's documented waypoint and error controls are described in
[the official quadgk reference](https://www.mathworks.com/help/matlab/ref/quadgk.html).

```text
python strict/two-timescale-ma/validate_corrected_zf_position_python.py --job <unchanged-full-job.json> --config <unchanged-run-config.json> --output <new-python-v3.json>
python strict/two-timescale-ma/compare_corrected_positions.py --python <new-python-v3.json> --matlab <new-matlab-v3.json> --output <new-paired-v3.json>
```

```matlab
validate_corrected_zf_position_matlab('new-matlab-v3.json', ...
    'unchanged-full-job.json','unchanged-run-config.json');
```

## 简要结论

保留论文原信道和完整1000样本，修正的是同一个严格推导积分的数值计算。
旧失败证据仍保留；新版应以实际双语言逐项验证结果为准。
完整图14/16仍需要各自全部300个几何场景和每个接受位置的证据，不能由单点测试代替。
