# Versioned MATLAB corrected-source Figs.14/16 adapter

This separate directory bridges actual **MATLAB-full-v2** source trajectories
to the already tested original-model segmented Laplace integral. It does not
edit the live MA Python engine, the old MATLAB receipts/fingerprints, or any
original integral/context/position helper. Old MATLAB startup-error files
cannot be relabeled as new source trajectories.

Add both paths from the repository root:

```matlab
addpath('strict/two-timescale-ma');
addpath('strict/matlab-corrected-source-v2');
% One actual complete1000-draw initial-position preflight, not a full figure:
validate_corrected_zf_position_matlab_source_v2('n6-position-new-adapter.json', ...
    'output/figure16/jobs/case-000-mc-000.json','output/figure16/run_config.json');
% Full source execution, then every accepted position, only after all300 pass:
run_corrected_ma_figure_matlab_source_v2('output/figure16/jobs', ...
    'output/figure16/matlab-full-v2','output/figure16/corrected-matlab-source-v2', ...
    'output/figure16/run_config.json',true);
```

The input manifest must contain all three κ5/10/15dB cases,100 geometries per
case and1000 unchanged NLoS samples. The100/1000 counts are disclosed configured
choices, not claimed as recovered author Monte Carlo counts. Full N8/M5 Fig14
and N6/M5 Fig16 remain separate domains. Every source receipt must carry the
actual new entry fingerprint, the original criterion stops and finite coordinate
certificates; all accepted positions are checked for spacing and box constraints.
The adapter never reoptimizes a position using the corrected bound.

After the **entire300-source-job gate** passes, both original channel models
are evaluated at every accepted position with all1000 samples, retaining the
individual MC rates, conditional moments and quadrature error estimates. Five
panels keep the layout MC, population-Jensen plug-in, MC-minus-Jensen difference,
outer-MC delta standard error and quadrature estimate separate, with all six
model/κ legend series. Quadrature error estimates are not interval certificates;
a population Jensen theorem is not a finite-ensemble lower-bound guarantee.
Final-state hold across unequal trajectories is disclosed explicitly.

The separate source-only proof is
[here](../validation/two-timescale-ma-corrected-zf/corrected-matlab-source-v2-source-only-proof.json).
It establishes the unchanged evaluation loop and frozen dependencies, **not an
actual new-adapter MATLAB test or completion of either full300 bank**. That
historical source-only receipt remains unchanged. New actual native N6/N8
full1000 initial-position tests now pass separately; see
[their complete numerical inputs and receipts](../validation/two-timescale-ma-corrected-source-v2-position-components/README.md).
They do not verify either full300 source trajectory bank. The central entry
now selects this new adapter rather than the incompatible old source-v1 schema.
Printed Eq74/75 recovery and historical figure closeness remain unclaimed.
