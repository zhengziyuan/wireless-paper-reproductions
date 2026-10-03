# Same Euclidean cone: exact raw-order component regression

This folder contains exact byte-for-byte copies of the independently executed
MATLAB WORK component and its shared fixtures, plus its actual numerical
receipt and an explicitly redacted compact runtime binder. It is
outside the live scientific package fingerprint. The v1 helper is retained
solely as an explicit failing implementation control, not as a recommended
solver. No author source or raw author simulation code is included.

The fresh native run passed the original 1010 shared checks and six strict
small-component checks (three scales, both low/high optional orders), while
reproducing three errors in the v1 implementation. Before/after runtime binding
and the component output SHA256 are in
`sorted_cone_v2_native_binding-redacted-public-v1.json`. Only private machine
workspace prefixes have been removed; all hashes and numerical assertions are
preserved. The untouched raw binder remains in private WORK with SHA256
`774c9212535984985b8cc53348f69eef503f6946d9494dce51f20cf2c968aad5`.
The original
row-scale fixture bounds alone were too coarse to detect those small-coordinate
errors.

The only v2 numerical difference is re-sorting the original raw binary optional
values inside the exact uncertain-row fallback. Rounded centered values can
tie when the raw values differ. The Euclidean cone, its mandatory positive
support, raw direction, metric, and stopping tolerances are unchanged. Tiny
positive directions are not pruned. Exact membership is compared before the
last conversion to floating-point output.

To rerun in native MATLAB, select this folder and use fresh output paths:

```matlab
componentDir = pwd; % This folder, not the live mis-sensing package.
addpath(componentDir);
outputDir = tempname;
mkdir(outputDir);
b = run_sorted_cone_v2_bound_regression( ...
    fullfile(componentDir,'sorted_cone_shared_exact_fixture.json'), ...
    fullfile(componentDir,'matlab_centered_optional_order_exact_counterexamples.json'), ...
    fullfile(outputDir,'component.json'), ...
    fullfile(outputDir,'binding.json'));
assert(b.all_checks_pass);
assert(strcmp(b.source_sha256_before.binding_wrapper, ...
    'e3dcbcec78963b0aebc4dafefee4229efd5f9235902e2a0d0030743c96f77c09'));
```

The bundled MATLAB JVM is required for exact stored-binary BigDecimal fallback
and source hashing; the Symbolic Math Toolbox is not required. MATLAB runtime
paths differ when rerunning this portable copy, so a rerun produces a new
binding receipt. The numerical receipt and redacted binder describe the actual earlier WORK
execution, not an execution retrospectively performed in this folder.

This verifies a projection component. It does not certify global convergence,
the original 4000-iteration inner requirement, a complete 30-outer MATLAB
trajectory, all 6000 starts, original figure agreement, or live-v4 promotion.
